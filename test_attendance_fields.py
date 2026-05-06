import requests
import json

# Test attendance history API
login_data = {'email': 'shailesh@gmail.com', 'password': '12345678'}
resp = requests.post('http://localhost:5000/api/auth/login', json=login_data)

if resp.status_code == 200:
    token = resp.json().get('token')
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get attendance history
    resp = requests.get('http://localhost:5000/api/attendance/history', headers=headers)
    data = resp.json()
    
    if 'history' in data and data['history']:
        record = data['history'][0]
        print("Sample record fields:")
        for key in ['id', 'lecture_date', 'start_time', 'end_time', 'end_time_actual', 'status']:
            print(f"  {key}: {record.get(key)}")
    else:
        print("No history data")
