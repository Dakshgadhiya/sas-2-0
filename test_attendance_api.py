import requests
import json

# Test attendance history API
login_data = {'email': 'shailesh@gmail.com', 'password': '12345678'}
resp = requests.post('http://localhost:5000/api/auth/login', json=login_data)
print(f'✓ Login: {resp.status_code}')

if resp.status_code == 200:
    token = resp.json().get('token')
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get attendance history
    resp = requests.get('http://localhost:5000/api/attendance/history', headers=headers)
    print(f'✓ History API: {resp.status_code}')
    
    data = resp.json()
    print(f'Response: {json.dumps(data, indent=2)[:200]}')
    
    if 'history' in data:
        history = data['history']
        print(f'✓ Records found: {len(history)}')
        
        if history:
            for i, record in enumerate(history[:3]):
                print(f'  {i+1}. {record.get("lecture_subject")} - {record.get("status").upper()}')
    else:
        print(f'✗ No history key in response')
else:
    print(f'✗ Login failed: {resp.json()}')
