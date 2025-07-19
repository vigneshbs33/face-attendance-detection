import requests
import json
import os
from datetime import datetime

def test_file_upload():
    """Test the file upload functionality"""
    try:
        # Test the registration API with file upload
        url = 'http://localhost:5000/api/register'
        
        # Check if we have a test image in uploads folder
        test_image_path = None
        if os.path.exists('uploads'):
            for file in os.listdir('uploads'):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    test_image_path = os.path.join('uploads', file)
                    break
        
        if not test_image_path:
            print("No test image found in uploads folder. Creating a simple test...")
            # Test with a simple text file to verify validation
            test_data = {
                'name': 'test_user',
                'image': 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A'
            }
            
            response = requests.post(url, json=test_data)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success: {data.get('success')}")
                print(f"Message: {data.get('message')}")
            else:
                print(f"Error: {response.status_code}")
                
        else:
            print(f"Testing with file: {test_image_path}")
            
            # Test file upload
            with open(test_image_path, 'rb') as f:
                files = {'file': f}
                data = {'name': 'test_user_upload'}
                
                response = requests.post(url, files=files, data=data)
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Success: {data.get('success')}")
                    print(f"Message: {data.get('message')}")
                else:
                    print(f"Error: {response.status_code}")
        
        # Test registered faces API
        print("\n--- Testing Registered Faces API ---")
        faces_response = requests.get('http://localhost:5000/api/registered-faces')
        print(f"Status Code: {faces_response.status_code}")
        
        if faces_response.status_code == 200:
            faces_data = faces_response.json()
            print(f"Success: {faces_data.get('success')}")
            print(f"Registered faces: {faces_data.get('faces')}")
        else:
            print(f"Error: {faces_response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure the Flask app is running.")
    except Exception as e:
        print(f"Error: {e}")

def test_attendance_api():
    """Test the attendance API"""
    try:
        response = requests.get('http://localhost:5000/api/attendance-list')
        print(f"\n--- Testing Attendance API ---")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Attendance data: {data.get('attendance')}")
        else:
            print(f"Error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure the Flask app is running.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print(f"Testing file upload functionality at {datetime.now()}")
    print("=" * 50)
    
    test_file_upload()
    test_attendance_api()
    
    print("\n" + "=" * 50)
    print("Test completed!") 