import json
import urllib.request
import urllib.error

base = 'http://127.0.0.1:5000'
reg_data = {'name': 'Test Faculty','faculty_id': 'TFTEST','email': 'testfaculty123@example.com','password': 'pass123','role': 'faculty'}
req = urllib.request.Request(base + '/api/auth/register', data=json.dumps(reg_data).encode(), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode())
        print('register ok', body)
        token = body['token']
except urllib.error.HTTPError as he:
    print('register failed', he.code, he.read().decode())
    raise SystemExit(1)
except Exception as e:
    print('register failed exception', e)
    raise SystemExit(1)

session_data = {
    'lecture_title': 'Test','subject': 'Debug','date': '2026-04-28','start_time': '2026-04-28T23:00:00','end_time':'2026-04-28T23:30:00','latitude':21.180215,'longitude':72.81738,'radius':20,'mode':'OFFLINE','join_url':''
}
req = urllib.request.Request(base + '/api/lectures/sessions', data=json.dumps(session_data).encode(), headers={'Content-Type':'application/json','Authorization': f'Bearer {token}'}, method='POST')
try:
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode())
        print('create ok', body)
except urllib.error.HTTPError as he:
    print('create failed', he.code, he.read().decode())
except Exception as e:
    print('create failed exception', e)
