import json
import urllib.request
import urllib.error
import time

base = 'http://127.0.0.1:5000'
reg_data = {
    'name': 'APITest Faculty',
    'faculty_id': f'APIFAC{int(time.time())}',
    'email': f'apifac{int(time.time())}@test.com',
    'password': 'pass123',
    'role': 'faculty'
}

req = urllib.request.Request(
    base + '/api/auth/register',
    data=json.dumps(reg_data).encode(),
    headers={'Content-Type': 'application/json'}
)
try:
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode())
        token = body['token']
        print('registered', body)
except urllib.error.HTTPError as he:
    print('register failed', he.code, he.read().decode())
    raise

session_data = {
    'lecture_title': 'API Test',
    'subject': 'Debug',
    'date': '2026-04-29',
    'start_time': '2026-04-29T10:00:00',
    'end_time': '2026-04-29T11:00:00',
    'latitude': 21.226073,
    'longitude': 72.842933,
    'radius': 20,
    'mode': 'OFFLINE',
    'join_url': ''
}
req = urllib.request.Request(
    base + '/api/lectures/sessions',
    data=json.dumps(session_data).encode(),
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    },
    method='POST'
)
try:
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode())
        print('create ok', body)
except urllib.error.HTTPError as he:
    print('create failed', he.code, he.read().decode())
