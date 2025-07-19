// Face Attendance System - Frontend JavaScript

class FaceAttendanceApp {
    constructor() {
        // DOM Elements
        this.video = document.getElementById('video');
        this.canvas = document.getElementById('canvas');
        this.ctx = this.canvas.getContext('2d');
        
        // State
        this.stream = null;
        this.capturedImage = null;
        this.socket = null;
        this.isCameraOn = false;
        this.isDetecting = false;
        this.detectionInterval = null;
        
        // Initialization
        this.initializeSocket();
        this.initializeEventListeners();
        this.loadInitialData();
        this.requestNotificationPermission();
    }

    initializeSocket() {
        try {
            this.socket = io({ transports: ['websocket'] });

            this.socket.on('connect', () => this.updateConnectionStatus(true));
            this.socket.on('disconnect', () => this.updateConnectionStatus(false));
            this.socket.on('face_detected', (data) => this.handleFaceDetection(data));
            this.socket.on('status', (data) => console.log('Server Status:', data.message));
            this.socket.on('server_error', (data) => {
                console.error(`Server Error: ${data.message}`);
                this.stopDetection();
            });

        } catch (error) {
            console.error("Socket.IO connection failed:", error);
            this.showNotification("Could not connect to the live server.", "error");
        }
    }
    
    updateConnectionStatus(isConnected) {
        const statusEl = document.getElementById('connectionStatus');
        if (isConnected) {
            console.log('Connected to server');
            statusEl.textContent = 'Connected';
            statusEl.className = 'status-value text-success';
        } else {
            console.log('Disconnected from server');
            statusEl.textContent = 'Disconnected';
            statusEl.className = 'status-value text-danger';
        }
    }

    async requestNotificationPermission() {
        if ('Notification' in window && Notification.permission !== 'granted') {
            await Notification.requestPermission();
        }
    }

    handleFaceDetection(data) {
        if (data.message === 'No face detected') {
            return;
        }
        this.showNotificationArea();
        this.addLiveNotification(data);
        // this.showBrowserNotification(data); // Computer notification disabled
        this.playNotificationSound();
        this.loadAttendance(); // Refresh attendance list
    }

    showNotificationArea(show = true) {
        document.getElementById('notificationArea').style.display = show ? 'block' : 'none';
    }

    addLiveNotification(data) {
        const container = document.getElementById('liveNotifications');
        const notification = document.createElement('div');
        notification.className = 'live-notification attendance';
        
        notification.innerHTML = `
            <div class="live-notification-header">
                <span class="live-notification-name">${data.name}</span>
                <span class="live-notification-time">${data.time}</span>
            </div>
            <p class="live-notification-message">${data.message}</p>
        `;
        
        container.insertBefore(notification, container.firstChild);
        
        // Limit to 10 notifications
        if (container.children.length > 10) {
            container.removeChild(container.lastChild);
        }
    }

    showBrowserNotification(data) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const notification = new Notification('Face Detected!', {
                body: `${data.name} - ${data.message}`,
                icon: '/static/favicon.ico', // Optional: add an icon
                silent: false
            });
            setTimeout(() => notification.close(), 5000);
        }
    }

    playNotificationSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
            
            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.15);
        } catch (error) {
            console.error("Could not play notification sound:", error);
        }
    }

    initializeEventListeners() {
        document.getElementById('startCamera').addEventListener('click', () => this.startCamera());
        document.getElementById('capturePhoto').addEventListener('click', () => this.capturePhoto());
        document.getElementById('registerFace').addEventListener('click', () => this.registerFace());
        document.getElementById('startDetection').addEventListener('click', () => this.startDetection());
        document.getElementById('stopDetection').addEventListener('click', () => this.stopDetection());
        document.getElementById('refreshAttendance').addEventListener('click', () => this.loadAttendance());
        document.getElementById('refreshFaces').addEventListener('click', () => this.loadRegisteredFaces());
        
        // File upload handling
        document.getElementById('fileUpload').addEventListener('change', (e) => this.handleFileUpload(e));
        document.getElementById('clearFileUpload').addEventListener('click', () => this.clearFileUpload());
        
        document.getElementById('nameInput').addEventListener('input', (e) => {
            this.updateRegisterButton();
        });
    }

    async startCamera() {
        console.log('Attempting to start camera...');
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480, facingMode: 'user' } });
            this.video.srcObject = this.stream;
            await this.video.play();
            
            this.isCameraOn = true;
            this.updateCameraUI(true);
            this.showNotification('Camera started successfully', 'success');
        } catch (error) {
            console.error('Error starting camera:', error);
            this.showNotification('Error starting camera: ' + error.message, 'error');
        }
    }
    
    updateCameraUI(isOnline) {
        document.getElementById('startCamera').disabled = isOnline;
        document.getElementById('capturePhoto').disabled = !isOnline;
        document.getElementById('startDetection').disabled = !isOnline;
        document.getElementById('stopDetection').disabled = true;
        document.getElementById('cameraStatus').textContent = isOnline ? 'Online' : 'Offline';
        document.getElementById('cameraStatus').className = `status-value text-${isOnline ? 'success' : 'danger'}`;
    }

    capturePhoto() {
        if (!this.stream) return;
        this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        this.capturedImage = this.canvas.toDataURL('image/jpeg', 0.8);
        document.getElementById('capturedPhoto').src = this.capturedImage;
        document.getElementById('capturedPhoto').style.display = 'block';
        this.updateRegisterButton();
        this.showNotification('Photo captured successfully', 'success');
    }

    handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith('image/')) {
            this.showNotification('Please select an image file.', 'error');
            event.target.value = '';
            return;
        }

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            this.showNotification('File size must be less than 5MB.', 'error');
            event.target.value = '';
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            this.capturedImage = e.target.result;
            document.getElementById('capturedPhoto').src = this.capturedImage;
            document.getElementById('capturedPhoto').style.display = 'block';
            
            // Show file name and clear button
            const fileNameDisplay = document.getElementById('fileNameDisplay');
            fileNameDisplay.textContent = `Selected: ${file.name}`;
            fileNameDisplay.style.display = 'block';
            
            document.getElementById('clearFileUpload').style.display = 'block';
            
            this.updateRegisterButton();
            this.showNotification('Image uploaded successfully', 'success');
        };
        reader.readAsDataURL(file);
    }

    updateRegisterButton() {
        const name = document.getElementById('nameInput').value.trim();
        const hasImage = this.capturedImage !== null;
        document.getElementById('registerFace').disabled = !name || !hasImage;
    }

    clearFileUpload() {
        document.getElementById('fileUpload').value = '';
        document.getElementById('fileNameDisplay').style.display = 'none';
        document.getElementById('clearFileUpload').style.display = 'none';
        document.getElementById('capturedPhoto').style.display = 'none';
        this.capturedImage = null;
        this.updateRegisterButton();
        this.showNotification('File upload cleared', 'info');
    }

    resetRegistrationForm() {
        document.getElementById('nameInput').value = '';
        document.getElementById('capturedPhoto').style.display = 'none';
        document.getElementById('fileUpload').value = '';
        document.getElementById('fileNameDisplay').style.display = 'none';
        document.getElementById('clearFileUpload').style.display = 'none';
        document.getElementById('registerFace').disabled = true;
        this.capturedImage = null;
    }

    async sendApiRequest(endpoint, method = 'GET', body = null) {
        try {
            const options = {
                method: method,
                headers: { 'Content-Type': 'application/json' },
            };
            if (body) {
                options.body = JSON.stringify(body);
            }
            const response = await fetch(endpoint, options);
            const result = await response.json();

            if (result.success) {
                this.showNotification(result.message || 'Operation successful', 'success');
            } else {
                this.showNotification(result.message || 'An error occurred', 'error');
            }
            return result;
        } catch (error) {
            console.error(`Error with ${endpoint}:`, error);
            this.showNotification(`API Error: ${error.message}`, 'error');
            return { success: false, message: error.message };
        }
    }

    async registerFace() {
        const name = document.getElementById('nameInput').value.trim();
        if (!name || !this.capturedImage) {
            this.showNotification('Please enter a name and provide an image.', 'error');
            return;
        }
        
        try {
            let result;
            
            // Check if we have a file upload or camera capture
            const fileInput = document.getElementById('fileUpload');
            if (fileInput.files.length > 0) {
                // File upload - use FormData
                const formData = new FormData();
                formData.append('name', name);
                formData.append('file', fileInput.files[0]);
                
                const response = await fetch('/api/register', {
                    method: 'POST',
                    body: formData
                });
                result = await response.json();
            } else {
                // Camera capture - use JSON with base64 image
                result = await this.sendApiRequest('/api/register', 'POST', { 
                    name: name, 
                    image: this.capturedImage 
                });
            }
            
            if (result.success) {
                // Clear form
                this.resetRegistrationForm();
                this.loadRegisteredFaces();
                this.showNotification(result.message || 'Face registered successfully', 'success');
            } else {
                this.showNotification(result.message || 'Registration failed', 'error');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showNotification('Registration failed: ' + error.message, 'error');
        }
    }

    async startDetection() {
        console.log('Attempting to start detection...');
        if (!this.isCameraOn) {
            this.showNotification('Please start the camera first.', 'error');
            return;
        }
        if (this.isDetecting) return;

        this.isDetecting = true;
        this.updateDetectionUI(true);
        this.showNotificationArea();

        this.detectionInterval = setInterval(() => {
            if (!this.isDetecting || !this.isCameraOn) {
                this.stopDetection();
                return;
            };
            
            this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
            const imageData = this.canvas.toDataURL('image/jpeg', 0.8);
            
            this.socket.emit('stream_frame', { image: imageData });

        }, 500);
    }

    async stopDetection() {
        if (!this.isDetecting) return;
        
        this.isDetecting = false;
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
            this.detectionInterval = null;
        }
        this.updateDetectionUI(false);
    }

    updateDetectionUI(isRunning) {
        document.getElementById('startDetection').disabled = isRunning;
        document.getElementById('stopDetection').disabled = !isRunning;
        document.getElementById('detectionStatus').textContent = isRunning ? 'Running' : 'Stopped';
        document.getElementById('detectionStatus').className = `status-value text-${isRunning ? 'success' : 'danger'}`;
    }

    async loadAttendance() {
        console.log('Loading attendance...');
        const res = await fetch('/api/attendance-list');
        const result = await res.json();
        console.log('Attendance API response:', result);
        if (result.success) {
            console.log('Displaying attendance:', result.attendance);
            this.displayAttendance(result.attendance);
        } else {
            console.error('Failed to load attendance:', result);
        }
    }

    displayAttendance(records) {
        console.log('displayAttendance called with:', records);
        const container = document.getElementById('attendanceList');
        console.log('Container element:', container);
        if (Object.keys(records).length === 0) {
            console.log('No attendance records, showing empty message');
            container.innerHTML = '<p class="text-muted">No attendance records for today</p>';
            return;
        }
        console.log('Creating attendance HTML for', Object.keys(records).length, 'records');
        container.innerHTML = Object.entries(records).map(([name, time]) => `
            <div class="attendance-item">
                <span class="attendance-name">${name}</span>
                <span class="attendance-time">${time}</span>
            </div>
        `).join('');
        console.log('Attendance HTML set:', container.innerHTML);
    }

    async loadRegisteredFaces() {
        const result = await this.sendApiRequest('/api/registered-faces');
        if (result.success) {
            this.displayRegisteredFaces(result.faces);
        }
    }

    displayRegisteredFaces(faces) {
        const container = document.getElementById('registeredFacesList');
        document.getElementById('registeredCount').textContent = faces.length;
        if (faces.length === 0) {
            container.innerHTML = '<p class="text-muted">No faces registered</p>';
            return;
        }
        container.innerHTML = faces.map(face => `
            <div class="face-item">
                <span class="face-name">${face}</span>
                <button class="delete-face-btn" onclick="app.deleteFace('${face}')" title="Delete face">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `).join('');
    }

    async deleteFace(name) {
        if (confirm(`Are you sure you want to delete the face registration for ${name}?`)) {
            await this.sendApiRequest('/api/delete-face', 'DELETE', { name: name });
            this.loadRegisteredFaces();
        }
    }

    loadInitialData() {
        this.loadAttendance();
        this.loadRegisteredFaces();
    }

    showNotification(message, type = 'info') {
        const toast = new bootstrap.Toast(document.getElementById('notificationToast'));
        const toastMessage = document.getElementById('toastMessage');
        toastMessage.textContent = message;
        toastMessage.className = `toast-body ${type === 'success' ? 'success-message' : type === 'error' ? 'error-message' : ''}`;
        toast.show();
    }
}

function hideNotificationArea() {
    document.getElementById('notificationArea').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new FaceAttendanceApp();
}); 