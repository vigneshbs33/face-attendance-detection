import os
import io
import base64
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
import face_recognition
from PIL import Image
from flask_socketio import SocketIO, emit
import eventlet
import numpy as np
import threading
import time

UPLOAD_FOLDER = 'uploads'
REGISTERED_FACES_FILE = 'registered_faces.json'
ATTENDANCE_FILE = 'attendance.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global cache for performance
registered_faces_cache = {}
attendance_cache = {}
last_cache_update = 0
cache_lock = threading.Lock()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return default

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def get_face_encoding(image):
    encodings = face_recognition.face_encodings(image)
    if encodings:
        return encodings[0]
    return None

def get_cached_faces():
    """Get cached registered faces, reload if needed"""
    global registered_faces_cache, last_cache_update
    current_time = time.time()
    
    with cache_lock:
        # Reload cache every 30 seconds or if empty
        if (current_time - last_cache_update > 30 or 
            not registered_faces_cache):
            registered_faces_cache = load_json(REGISTERED_FACES_FILE, {})
            last_cache_update = current_time
    
    return registered_faces_cache

def get_cached_attendance():
    """Get cached attendance data, reload if needed"""
    global attendance_cache
    today = datetime.now().strftime('%Y-%m-%d')
    
    with cache_lock:
        if today not in attendance_cache:
            attendance_cache = load_json(ATTENDANCE_FILE, {})
    
    return attendance_cache

def update_attendance_cache(name, timestamp):
    """Update attendance cache and save to file"""
    global attendance_cache
    today = datetime.now().strftime('%Y-%m-%d')
    
    with cache_lock:
        if today not in attendance_cache:
            attendance_cache[today] = {}
        attendance_cache[today][name] = timestamp
        
        # Save to file asynchronously
        def save_async():
            save_json(ATTENDANCE_FILE, attendance_cache)
        
        # Run save in background thread
        threading.Thread(target=save_async, daemon=True).start()

def get_image_from_request():
    if request.files:
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            img = face_recognition.load_image_file(file)
            return img, file.filename
    if request.form:
        image_data = request.form.get('image')
        if image_data and image_data.startswith('data:image'):
            header, encoded = image_data.split(',', 1)
            img_bytes = base64.b64decode(encoded)
            img = face_recognition.load_image_file(io.BytesIO(img_bytes))
            return img, 'webcam.jpg'
    if request.is_json:
        data = request.get_json()
        image_data = data.get('image')
        if image_data and image_data.startswith('data:image'):
            header, encoded = image_data.split(',', 1)
            img_bytes = base64.b64decode(encoded)
            img = face_recognition.load_image_file(io.BytesIO(img_bytes))
            return img, 'webcam.jpg'
    return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    name = request.form.get('name') or (request.get_json() or {}).get('name')
    if not name:
        return jsonify({'success': False, 'message': 'Name is required.'})
    img, filename = get_image_from_request()
    if img is None:
        return jsonify({'success': False, 'message': 'No valid image provided.'})
    encoding = get_face_encoding(img)
    if encoding is None:
        return jsonify({'success': False, 'message': 'No face detected in the image.'})
    
    # Update cache and save to file
    with cache_lock:
        registered_faces_cache[name] = encoding.tolist()
        save_json(REGISTERED_FACES_FILE, registered_faces_cache)
    
    # Save image for reference
    img_pil = Image.fromarray(img)
    img_path = os.path.join(UPLOAD_FOLDER, secure_filename(f'{name}.jpg'))
    img_pil.save(img_path)
    return jsonify({'success': True, 'message': f'Registered {name} successfully.'})

@app.route('/api/registered-faces')
def registered_faces():
    faces = get_cached_faces()
    return jsonify({'success': True, 'faces': list(faces.keys())})

def parse_attendance_time(time_str):
    try:
        # Try ISO format first
        return datetime.fromisoformat(time_str)
    except ValueError:
        # Fallback: time-only string, combine with today
        today = datetime.now().date()
        try:
            t = datetime.strptime(time_str, '%H:%M:%S').time()
            return datetime.combine(today, t)
        except Exception:
            print(f"Warning: Could not parse time string: {time_str}")
            return None

@app.route('/api/attendance', methods=['POST'])
def mark_attendance():
    img, filename = get_image_from_request()
    if img is None:
        return jsonify({'success': False, 'message': 'No valid image provided.'})
    encoding = get_face_encoding(img)
    if encoding is None:
        return jsonify({'success': False, 'message': 'No face detected in the image.'})
    
    faces = get_cached_faces()
    names = list(faces.keys())
    encodings = [np.array(faces[n]) for n in names]
    matches = face_recognition.compare_faces(encodings, encoding, tolerance=0.5)
    matched_name = None
    for i, match in enumerate(matches):
        if match:
            matched_name = names[i]
            break
    
    now = datetime.now()
    if matched_name:
        attendance = get_cached_attendance()
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in attendance:
            attendance[today] = {}
        
        last_time_str = attendance[today].get(matched_name)
        if last_time_str:
            last_time = parse_attendance_time(last_time_str)
            if last_time and (now - last_time) < timedelta(seconds=10):
                return jsonify({'success': True, 'message': f'Attendance marked for {matched_name}.'})
        
        update_attendance_cache(matched_name, now.isoformat())
        return jsonify({'success': True, 'message': f'Attendance marked for {matched_name}.'})
    else:
        return jsonify({'success': False, 'message': 'Face not recognized.'})

@app.route('/api/attendance-list')
def attendance_list():
    today = datetime.now().strftime('%Y-%m-%d')
    attendance = get_cached_attendance()
    today_attendance = attendance.get(today, {})
    result = {}
    for name, time_str in today_attendance.items():
        dt = parse_attendance_time(time_str)
        if dt:
            result[str(name)] = dt.strftime('%H:%M:%S')
        else:
            result[str(name)] = str(time_str)
    return jsonify({'success': True, 'attendance': result})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Frame rate limiting for real-time processing
last_processed_frame = {}
frame_processing_interval = 0.5  # Process every 0.5 seconds

@socketio.on('stream_frame')
def handle_stream_frame(data):
    current_time = time.time()
    session_id = request.sid
    
    # Rate limiting: only process frames every 0.5 seconds per session
    if (session_id in last_processed_frame and 
        current_time - last_processed_frame[session_id] < frame_processing_interval):
        return
    
    last_processed_frame[session_id] = current_time
    
    image_data = data.get('image')
    if not image_data or not image_data.startswith('data:image'):
        emit('server_error', {'message': 'Invalid image data'})
        return
    
    try:
        header, encoded = image_data.split(',', 1)
        img_bytes = base64.b64decode(encoded)
        img = face_recognition.load_image_file(io.BytesIO(img_bytes))
        encoding = get_face_encoding(img)
        
        if encoding is None:
            emit('face_detected', {
                'name': 'Unknown', 
                'message': 'No face detected', 
                'time': datetime.now().strftime('%H:%M:%S')
            })
            return
        
        # Use cached faces for faster processing
        faces = get_cached_faces()
        names = list(faces.keys())
        encodings = [np.array(faces[n]) for n in names]
        matches = face_recognition.compare_faces(encodings, encoding, tolerance=0.5)
        
        matched_name = None
        for i, match in enumerate(matches):
            if match:
                matched_name = names[i]
                break
        
        now = datetime.now()
        if matched_name:
            attendance = get_cached_attendance()
            today = datetime.now().strftime('%Y-%m-%d')
            if today not in attendance:
                attendance[today] = {}
            
            last_time_str = attendance[today].get(matched_name)
            if last_time_str:
                last_time = parse_attendance_time(last_time_str)
                if last_time and (now - last_time) < timedelta(seconds=10):
                    return  # Silently ignore during cooldown
            
            # Update attendance asynchronously
            update_attendance_cache(matched_name, now.isoformat())
            emit('face_detected', {
                'name': matched_name, 
                'message': f'{matched_name} marked present', 
                'time': now.strftime('%H:%M:%S')
            })
        else:
            emit('face_detected', {
                'name': 'Unknown', 
                'message': 'Unknown face detected', 
                'time': now.strftime('%H:%M:%S')
            })
    
    except Exception as e:
        print(f"Error processing frame: {e}")
        emit('server_error', {'message': 'Error processing image'})

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    socketio.run(app, debug=True) 