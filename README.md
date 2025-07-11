# 🎯 Face Attendance Detection System

A real-time face recognition attendance system built with Flask, face_recognition library, and WebSocket for live detection. This system allows you to register faces and automatically mark attendance when recognized faces are detected through a webcam.

## ✨ Features

- **Real-time Face Detection**: Live webcam feed with instant face recognition
- **Face Registration**: Register new faces with names through webcam or file upload
- **Automatic Attendance Marking**: Automatically marks attendance when recognized faces are detected
- **WebSocket Integration**: Real-time communication for live detection updates
- **Responsive UI**: Modern, mobile-friendly interface with Bootstrap
- **Performance Optimized**: Caching system for faster face recognition
- **Attendance History**: View daily attendance records
- **Multiple Input Methods**: Support for webcam capture and file uploads
- **Cooldown Protection**: Prevents spam marking with intelligent cooldown system

## 🛠️ Technology Stack

- **Backend**: Flask (Python web framework)
- **Face Recognition**: face_recognition library (dlib-based)
- **Real-time Communication**: Flask-SocketIO
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **UI Framework**: Bootstrap 5
- **Image Processing**: Pillow (PIL)
- **Data Storage**: JSON files (simple, no database required)

## 📋 Prerequisites

Before running this application, make sure you have:

- **Python 3.7+** installed on your system
- **Webcam** for face detection and registration
- **Modern web browser** with WebRTC support
- **Good lighting** for accurate face recognition

### System Requirements

- **RAM**: Minimum 4GB (8GB recommended for better performance)
- **Storage**: 100MB free space
- **Camera**: Any webcam with 640x480 resolution or higher
- **OS**: Windows, macOS, or Linux

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/face-attendance-detection.git
cd face-attendance-detection
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: The `face_recognition` library requires `dlib`, which might need additional system dependencies:

#### On Windows:
```bash
pip install cmake
pip install dlib
pip install face_recognition
```

#### On macOS:
```bash
brew install cmake
pip install dlib
pip install face_recognition
```

#### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install cmake
sudo apt-get install libopenblas-dev liblapack-dev
sudo apt-get install libx11-dev libgtk-3-dev
pip install dlib
pip install face_recognition
```

### 3. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## 📖 Usage Guide

### 1. Access the Application

Open your web browser and navigate to `http://localhost:5000`

### 2. Register Faces

#### Method 1: Using Webcam
1. Click **"Start Camera"** to activate your webcam
2. Position your face clearly in the camera view
3. Click **"Capture Photo"** to take a snapshot
4. Enter your name in the **"Name"** field
5. Click **"Register Face"** to save your face data

#### Method 2: Using File Upload
1. Place face images in the `uploads/` folder
2. Run the registration script:
   ```bash
   python register_uploaded_faces.py
   ```
3. This will automatically register all faces from the uploads folder

### 3. Mark Attendance

#### Real-time Detection (Recommended)
1. Click **"Start Camera"** if not already started
2. Click **"Start Detection"** to begin real-time face recognition
3. The system will automatically detect and mark attendance for recognized faces
4. Live notifications will appear in the right panel
5. Click **"Stop Detection"** to stop the process

#### Manual Attendance
1. Click **"Start Camera"**
2. Click **"Capture Photo"** to take a photo
3. The system will automatically attempt to recognize and mark attendance

### 4. View Attendance

- **Today's Attendance**: Shows current day's attendance records
- **Refresh Button**: Updates the attendance list
- **Time Display**: Shows exact time when attendance was marked

### 5. Manage Registered Faces

- View all registered faces in the **"Registered Faces"** section
- Refresh the list using the **"Refresh"** button
- Delete faces by clicking the delete icon (if implemented)

## 🔧 Configuration

### File Structure
```
face-attendance-detection/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── register_uploaded_faces.py  # Bulk face registration script
├── test_attendance.py          # API testing script
├── registered_faces.json       # Stored face encodings
├── attendance.json            # Attendance records
├── uploads/                   # Face images storage
├── templates/
│   └── index.html            # Main web interface
└── static/
    ├── css/
    │   └── style.css         # Custom styles
    └── js/
        └── app.js            # Frontend JavaScript
```

### Key Configuration Options

In `app.py`, you can modify:

```python
# Face recognition tolerance (lower = more strict)
tolerance=0.5

# Cooldown period between attendance marks (seconds)
timedelta(seconds=10)

# Frame processing interval for real-time detection (seconds)
frame_processing_interval = 0.5

# Cache refresh interval (seconds)
current_time - last_cache_update > 30
```

## 🧪 Testing

### Test the API
```bash
python test_attendance.py
```

This script tests the attendance API endpoints and displays results.

### Manual Testing
1. Register multiple faces
2. Test real-time detection
3. Verify attendance records
4. Check cooldown functionality

## 🔍 Troubleshooting

### Common Issues

#### 1. Camera Not Working
- **Solution**: Check browser permissions for camera access
- **Alternative**: Use file upload method for registration

#### 2. Face Recognition Not Accurate
- **Solution**: Ensure good lighting and clear face visibility
- **Tip**: Register multiple angles of the same face for better accuracy

#### 3. Slow Performance
- **Solution**: Reduce frame processing interval in `app.py`
- **Tip**: Close other applications to free up system resources

#### 4. Installation Errors
- **dlib issues**: Install system dependencies first
- **Permission errors**: Use virtual environment or run with appropriate permissions

#### 5. WebSocket Connection Issues
- **Solution**: Check firewall settings
- **Alternative**: Use HTTP polling instead of WebSocket

### Performance Optimization

1. **Reduce Image Quality**: Lower webcam resolution for faster processing
2. **Adjust Tolerance**: Increase tolerance for faster but less accurate recognition
3. **Cache Management**: Clear cache files if system becomes slow
4. **Frame Rate**: Adjust `frame_processing_interval` based on your system

## 📊 API Endpoints

### REST API
- `GET /` - Main web interface
- `POST /api/register` - Register new face
- `GET /api/registered-faces` - Get list of registered faces
- `POST /api/attendance` - Mark attendance manually
- `GET /api/attendance-list` - Get today's attendance
- `GET /uploads/<filename>` - Serve uploaded images

### WebSocket Events
- `stream_frame` - Send webcam frame for real-time detection
- `face_detected` - Receive face detection results
- `server_error` - Receive error notifications

## 🔒 Security Considerations

- **Local Deployment**: This system is designed for local/private network use
- **No Authentication**: Add user authentication for production use
- **Data Privacy**: Face data is stored locally in JSON format
- **HTTPS**: Use HTTPS in production environments

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [face_recognition](https://github.com/ageitgey/face_recognition) library by Adam Geitgey
- [Flask](https://flask.palletsprojects.com/) web framework
- [Bootstrap](https://getbootstrap.com/) for UI components
- [Socket.IO](https://socket.io/) for real-time communication

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Search existing [Issues](https://github.com/yourusername/face-attendance-detection/issues)
3. Create a new issue with detailed information about your problem

## 🔄 Updates

### Version 1.0.0
- Initial release with basic face recognition
- Real-time attendance marking
- Web interface with camera support
- Performance optimizations with caching
- Cooldown protection system

---

**Made with ❤️ for efficient attendance management**
