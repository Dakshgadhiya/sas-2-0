import urllib.request
import json

try:
    req = urllib.request.Request(
        'http://localhost:5000/api/admin/reset-database',
        method='POST',
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        print(f"Status Code: {response.status}")
        print(f"Response: {result}")
except Exception as e:
    print(f"Error: {e}")