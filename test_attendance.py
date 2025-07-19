import requests
import json
from datetime import datetime

def test_attendance_api():
    try:
        # Test the attendance API
        response = requests.get('http://localhost:5000/api/attendance-list')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Attendance data: {data.get('attendance')}")
            
            # Check if attendance data exists
            attendance = data.get('attendance', {})
            if attendance:
                print(f"Found {len(attendance)} attendance records:")
                for name, time in attendance.items():
                    print(f"  - {name}: {time}")
            else:
                print("No attendance records found")
        else:
            print(f"Error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure the Flask app is running.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print(f"Testing attendance API at {datetime.now()}")
    test_attendance_api() 