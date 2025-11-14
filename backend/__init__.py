import logging
import re
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_compress import Compress

from .routes.auth import bp_auth
from .routes.releases import bp_releases
from .routes.scanner import bp_scanner

def create_app():
    app = Flask(__name__)
    # Enable gzip compression
    Compress(app)
    
    # Configure CORS
    CORS(
        app,
        resources={
            r"/*": {
                "origins": [
                    "https://stracker-eta.vercel.app",
                    re.compile(r"http://localhost:\\d+"),
                    re.compile(r"http://127\.0\.0\.1:\\d+"),
                ],
                "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
        supports_credentials=True,
        always_send=True,
    )
    
    # Ensure CORS headers are present on all responses (including preflights)
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        # Allow Vercel deployment and local dev hosts
        if origin and (
            origin == "https://stracker-eta.vercel.app"
            or origin.startswith("http://localhost:")
            or origin.startswith("http://127.0.0.1:")
        ):
            response.headers["Access-Control-Allow-Origin"] = origin
            # Ensure caches vary by Origin
            response.headers["Vary"] = "Origin"
        # Methods/headers and credentials for preflight and actual responses
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        
        # Add short-lived caching for safe GET endpoints
        if request.method == "GET" and request.path in ("/releases", "/admin/users", "/me"):
            response.headers["Cache-Control"] = "public, max-age=30"
            # Ensure authorization and origin affect cache key
            vary_val = response.headers.get("Vary") or ""
            extras = [v.strip() for v in vary_val.split(",") if v]
            for v in ["Authorization", "Origin"]:
                if v not in extras:
                    extras.append(v)
            if extras:
                response.headers["Vary"] = ", ".join(extras)
        return response
    
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
