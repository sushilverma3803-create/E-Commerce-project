import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models import db

# Import route blueprints
from auth import auth_bp
from product_routes import product_bp
from cart_routes import cart_bp
from order_routes import order_bp
from admin_routes import admin_bp

def create_app(config_class=Config):
    """Application factory initializing database, middleware, error handlers, and blueprints."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable Cross-Origin Resource Sharing (CORS)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize database
    db.init_app(app)

    # Register API Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(admin_bp)

    # ------------------------------------------------------------------------
    # System Health Check
    # ------------------------------------------------------------------------
    @app.route("/api/health", methods=["GET"])
    def health_check():
        db_status = "connected"
        try:
            db.session.execute(db.text("SELECT 1"))
        except Exception as e:
            db_status = f"disconnected: {str(e)}"

        return jsonify({
            "status": "online",
            "database": db_status,
            "version": "1.0.0"
        }), 200

    # ------------------------------------------------------------------------
    # Frontend SPA Delivery (Serves React app on port 5000 as well)
    # ------------------------------------------------------------------------
    dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        if path.startswith("api/"):
            return jsonify({"error": "Resource Not Found", "status": 404}), 404
        if os.path.exists(os.path.join(dist_dir, path)) and path != "":
            from flask import send_from_directory
            return send_from_directory(dist_dir, path)
        if os.path.exists(os.path.join(dist_dir, "index.html")):
            from flask import send_from_directory
            return send_from_directory(dist_dir, "index.html")
        return jsonify({
            "status": "online",
            "message": "Flask API running. Frontend available at http://localhost:5173",
            "api_health": "/api/health"
        }), 200

    # ------------------------------------------------------------------------
    # Global Error Handlers
    # ------------------------------------------------------------------------
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad Request", "message": str(error), "status": 400}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource Not Found", "status": 404}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"error": "HTTP Method Not Allowed", "status": 405}), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({"error": "Internal Server Error", "status": 500}), 500

    # ------------------------------------------------------------------------
    # Custom CLI Command to Initialize Tables (Optional Alternative to SQL Script)
    # ------------------------------------------------------------------------
    @app.cli.command("init-db")
    def init_db_command():
        """Create database tables defined in SQLAlchemy models."""
        with app.app_context():
            db.create_all()
            print("Database tables created successfully from SQLAlchemy models.")

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ["true", "1", "yes"]
    app.run(host="0.0.0.0", port=port, debug=debug)
