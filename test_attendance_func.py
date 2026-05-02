import sys
import json
sys.path.insert(0, '/Users/User/Downloads/SAS_2.0 (3)/SAS_2.0')

# Set up test environment
import os
os.chdir(r'c:\Users\User\Downloads\SAS_2.0 (3)\SAS_2.0')

from models.attendance_model import get_attendance_by_student

# Test with student ID 10 (from database)
result = get_attendance_by_student(10)
print(f"Result type: {type(result)}")
print(f"Result length: {len(result)}")
if result:
    print(f"\nFirst record:\n{json.dumps(result[0], indent=2, default=str)}")
else:
    print("No records returned")
