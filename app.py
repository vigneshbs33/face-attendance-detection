import os
import io
import base64
import json
import webbrowser
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
import face_recognition
from PIL import Image
from flask_socketio import SocketIO, emit
import eventlet
import numpy as np

UPLOAD_FOLDER = 'uploads'
REGISTERED_FACES_FILE = 'registered_faces.json'
ATTENDANCE_FILE = 'attendance.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

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
    faces = load_json(REGISTERED_FACES_FILE, {})
    faces[name] = encoding.tolist()
    save_json(REGISTERED_FACES_FILE, faces)
    # Save image for reference
    img_pil = Image.fromarray(img)
    img_path = os.path.join(UPLOAD_FOLDER, secure_filename(f'{name}.jpg'))
    img_pil.save(img_path)
    return jsonify({'success': True, 'message': f'Registered {name} successfully.'})

@app.route('/api/registered-faces')
def registered_faces():
    faces = load_json(REGISTERED_FACES_FILE, {})
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
    faces = load_json(REGISTERED_FACES_FILE, {})
    names = list(faces.keys())
    encodings = [np.array(faces[n]) for n in names]
    matches = face_recognition.compare_faces(encodings, encoding, tolerance=0.5)
    matched_name = None
    for i, match in enumerate(matches):
        if match:
            matched_name = names[i]
            break
    today = datetime.now().strftime('%Y-%m-%d')
    attendance = load_json(ATTENDANCE_FILE, {})
    if today not in attendance:
        attendance[today] = {}
    now = datetime.now()
    if matched_name:
        last_time_str = attendance[today].get(matched_name)
        if last_time_str:
            last_time = parse_attendance_time(last_time_str)
            if last_time and (now - last_time) < timedelta(seconds=10):
                return jsonify({'success': True, 'message': f'{matched_name} was just marked present. Please wait before marking again.'})
        attendance[today][matched_name] = now.isoformat()
        save_json(ATTENDANCE_FILE, attendance)
        return jsonify({'success': True, 'message': f'Attendance marked for {matched_name}.'})
    else:
        return jsonify({'success': False, 'message': 'Face not recognized.'})

@app.route('/api/attendance-list')
def attendance_list():
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"Fetching attendance for date: {today}")
    attendance = load_json(ATTENDANCE_FILE, {})
    print(f"All attendance data: {attendance}")
    today_attendance = attendance.get(today, {})
    print(f"Today's attendance: {today_attendance}")
    result = {}
    for name, time_str in today_attendance.items():
        print(f"Processing {name}: {time_str}")
        dt = parse_attendance_time(time_str)
        if dt:
            result[str(name)] = dt.strftime('%H:%M:%S')
        else:
            result[str(name)] = str(time_str)
        print(f"Result for {name}: {result[str(name)]}")
    print(f"Final result: {result}")
    return jsonify({'success': True, 'attendance': result})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@socketio.on('stream_frame')
def handle_stream_frame(data):
    image_data = data.get('image')
    if not image_data or not image_data.startswith('data:image'):
        emit('server_error', {'message': 'Invalid image data'})
        return
    header, encoded = image_data.split(',', 1)
    img_bytes = base64.b64decode(encoded)
    img = face_recognition.load_image_file(io.BytesIO(img_bytes))
    encoding = get_face_encoding(img)
    if encoding is None:
        # Only emit every 2 seconds to avoid spam
        if not hasattr(handle_stream_frame, 'last_emit') or (datetime.now() - handle_stream_frame.last_emit).total_seconds() > 2:
            emit('face_detected', {'name': 'Unknown', 'message': 'No face detected', 'time': datetime.now().strftime('%H:%M:%S')})
            handle_stream_frame.last_emit = datetime.now()
        return
    faces = load_json(REGISTERED_FACES_FILE, {})
    names = list(faces.keys())
    encodings = [np.array(faces[n]) for n in names]
    matches = face_recognition.compare_faces(encodings, encoding, tolerance=0.5)
    matched_name = None
    for i, match in enumerate(matches):
        if match:
            matched_name = names[i]
            break
    today = datetime.now().strftime('%Y-%m-%d')
    attendance = load_json(ATTENDANCE_FILE, {})
    if today not in attendance:
        attendance[today] = {}
    now = datetime.now()
    if matched_name:
        last_time_str = attendance[today].get(matched_name)
        if last_time_str:
            last_time = parse_attendance_time(last_time_str)
            if last_time and (now - last_time) < timedelta(seconds=10):
                return  # Cooldown: do not mark again
        attendance[today][matched_name] = now.isoformat()
        save_json(ATTENDANCE_FILE, attendance)
        emit('face_detected', {'name': matched_name, 'message': f'{matched_name} marked present', 'time': now.strftime('%H:%M:%S')})
    else:
        emit('face_detected', {'name': 'Unknown', 'message': 'Unknown face detected', 'time': now.strftime('%H:%M:%S')})

def open_browser():
    """Open the browser after a short delay to ensure the server is running"""
    time.sleep(1.5)  # Wait for server to start
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Start browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print("🚀 Starting Face Attendance System...")
    print("🌐 Opening browser automatically...")
    print("📱 Access the application at: http://localhost:5000")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 