import os
import json
import face_recognition
import numpy as np

UPLOAD_FOLDER = 'uploads'
REGISTERED_FACES_FILE = 'registered_faces.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

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

def main():
    faces = load_json(REGISTERED_FACES_FILE, {})
    for filename in os.listdir(UPLOAD_FOLDER):
        if allowed_file(filename):
            name = os.path.splitext(filename)[0]
            path = os.path.join(UPLOAD_FOLDER, filename)
            print(f'Processing {filename} as {name}...')
            img = face_recognition.load_image_file(path)
            encodings = face_recognition.face_encodings(img)
            if encodings:
                faces[name] = encodings[0].tolist()
                print(f'  Registered: {name}')
            else:
                print(f'  No face found in {filename}, skipping.')
    save_json(REGISTERED_FACES_FILE, faces)
    print('Done. All valid faces registered.')

if __name__ == '__main__':
    main() 