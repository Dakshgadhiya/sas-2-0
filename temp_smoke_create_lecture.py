import requests
url='http://localhost:5000/api/lectures/sessions'
headers={'Authorization':'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjI4LCJyb2xlIjoiZmFjdWx0eS2N0eSIsImlhdCI6MTc3ODA3NzE1MiwiZXhwIjoxNzc4MTYzNTUyfQ.6CyOwtb5JejRwmJdRY4YwEM2RP2hbXds8qgHXiTJxcs'}
# Overwrite with real token
headers['Authorization']='Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjI4LCJyb2xlIjoiZmFjdWx0eSIsImlhdCI6MTc3ODA3NzE1MiwiZXhwIjoxNzc4MTYzNTUyfQ.6CyOwtb5JejRwmJdRY4YwEM2RP2hbXds8qgHXiTJxcs'
payload={
  'lecture_title':'Smoke Test Lecture (API)',
  'subject':'Mathematics',
  'semester':'1',
  'date':'2026-05-07',
  'start_time':'2026-05-07T08:30:00+00:00',
  'end_time':'2026-05-07T09:30:00+00:00'
}
resp=requests.post(url, headers=headers, json=payload)
print('STATUS', resp.status_code)
try:
    print(resp.json())
except Exception:
    print(resp.text)
