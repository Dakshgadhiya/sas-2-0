import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS

# Ensure project root is in path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from backend import config
from backend.database import init_db, get_db
from backend.auto_seed import auto_seed_if_empty
from routes.auth_routes import auth_routes
from routes.lecture_routes import lecture_routes
from routes.attendance_routes import attendance_routes
from routes.admin_routes import admin_routes
from routes.notifications_routes import notifications_routes


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER

    CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers=["Content-Type", "Authorization"])

    # Create required folders
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(config.DATASET_FOLDER, exist_ok=True)
    os.makedirs(config.MODEL_FOLDER, exist_ok=True)

    # Init DB
    init_db()
    
    # Auto-seed if empty (for Render deployments)
    db = get_db()
    auto_seed_if_empty(db)
    db.close()

    # Register blueprints
    app.register_blueprint(auth_routes)
    app.register_blueprint(lecture_routes)
    app.register_blueprint(attendance_routes)
    app.register_blueprint(admin_routes)
    app.register_blueprint(notifications_routes)

    # Health check
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    @app.route("/", methods=["GET"])
    def root():
        return jsonify({"status": "backend_running"})

    return app


# ✅ IMPORTANT: expose app for Gunicorn (THIS FIXES YOUR ISSUE)
app = create_app()


# Optional local run only
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)