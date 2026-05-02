#!/usr/bin/env python
import sys
import os

# Add the project to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from backend.app import create_app
    app = create_app()
    print("✅ Flask app created successfully")
    print(f"✅ Routes registered: {len(app.url_map._rules)}")
    
    # Check if admin_routes is registered
    if 'admin_routes' in app.blueprints:
        print("✅ admin_routes blueprint registered")
    else:
        print("❌ admin_routes blueprint NOT registered")
    
    # List all registered blueprints
    print(f"✅ Blueprints: {', '.join(app.blueprints.keys())}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
