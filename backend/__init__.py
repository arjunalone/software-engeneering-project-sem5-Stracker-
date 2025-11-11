import logging
from flask import Flask, jsonify
from flask_cors import CORS

from .routes.auth import bp_auth
from .routes.releases import bp_releases
from .routes.scanner import bp_scanner

def create_app():
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, 
         resources={
             r"/*": {
                 "origins": [
                     "https://stracker-eta.vercel.app",
                     "http://localhost:5173"  # For local development
                 ],
                 "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization"]
             }
         },
         supports_credentials=True
    )
    
    logging.basicConfig(level=logging.INFO)

    # Health and root
    @app.get("/")
    def root_index():
        return jsonify({"ok": True, "service": "release-tracker-api"}), 200

    @app.get("/health")
    def health():
        return jsonify({"status": "healthy"}), 200

    # Blueprints
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_releases)
    app.register_blueprint(bp_scanner)

    return app
