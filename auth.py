import re
from functools import wraps
from datetime import datetime, timedelta
# pyrefly: ignore [missing-import]
import jwt
from flask import Blueprint, request, jsonify, current_app
from models import db, User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

def generate_token(user: User) -> str:
    """Generate JWT signed bearer token with user claims and expiration."""
    secret = current_app.config.get("JWT_SECRET_KEY", "fallback-secret")
    delta = current_app.config.get("JWT_EXPIRATION_DELTA", timedelta(hours=24))
    
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + delta,
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def decode_token(token: str) -> dict:
    """Decode and validate signature/expiration of JWT token."""
    secret = current_app.config.get("JWT_SECRET_KEY", "fallback-secret")
    return jwt.decode(token, secret, algorithms=["HS256"])

def jwt_required(f):
    """Decorator to enforce authenticated JWT access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization header is missing", "status": 401}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Invalid Authorization header format. Expected 'Bearer <token>'", "status": 401}), 401

        token = parts[1]
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
            user = User.query.get(user_id)
            if not user:
                return jsonify({"error": "User associated with this token no longer exists", "status": 401}), 401
            request.current_user = user
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired. Please log in again", "status": 401}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token signature or payload", "status": 401}), 401

        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to enforce admin role privilege."""
    @wraps(f)
    @jwt_required
    def decorated_function(*args, **kwargs):
        user = getattr(request, "current_user", None)
        if not user or user.role != "admin":
            return jsonify({
                "error": "Access forbidden: administrator privileges required",
                "status": 403
            }), 403
        return f(*args, **kwargs)
    return decorated_function

# ----------------------------------------------------------------------------
# Authentication Routes
# ----------------------------------------------------------------------------

@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new customer or admin user account."""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    phone = data.get("phone", "").strip() or None
    role = data.get("role", "customer").strip().lower()

    if not name or not email or not password:
        return jsonify({"error": "Fields 'name', 'email', and 'password' are required", "status": 400}), 400

    if not re.match(EMAIL_REGEX, email):
        return jsonify({"error": "Invalid email address format", "status": 400}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long", "status": 400}), 400

    if role not in ["customer", "admin"]:
        return jsonify({"error": "Role must be either 'customer' or 'admin'", "status": 400}), 400

    # Prevent duplicate email
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email address already exists", "status": 409}), 409

    user = User(
        name=name,
        email=email,
        role=role,
        phone=phone
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    token = generate_token(user)

    return jsonify({
        "message": "User registered successfully",
        "user": user.to_dict(),
        "token": token,
        "token_type": "Bearer"
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate credentials and issue JWT bearer token."""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Both 'email' and 'password' are required", "status": 400}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password credentials", "status": 401}), 401

    token = generate_token(user)

    return jsonify({
        "message": "Login successful",
        "user": user.to_dict(),
        "token": token,
        "token_type": "Bearer"
    }), 200

@auth_bp.route("/me", methods=["GET"])
@jwt_required
def get_current_user_profile():
    """Retrieve profile data for the authenticated session."""
    user = request.current_user
    return jsonify({
        "user": user.to_dict()
    }), 200
