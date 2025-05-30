from functools import wraps
from flask import request, jsonify, current_app, g
import jwt
from ..models import User # Assuming models.py is in the parent of app.utils

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1] # Bearer <token>
            except IndexError:
                return jsonify({"msg": "Bearer token malformed."}), 401

        if not token:
            return jsonify({"msg": "Token is missing."}), 401

        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            # Store user_id and role in g for potential use by role_required decorators or the route itself
            g.token_user_id = data.get('user_id')
            g.token_user_role = data.get('role') # Role from token
            
            current_user = User.query.get(g.token_user_id)
            if not current_user:
                return jsonify({"msg": "User not found for token."}), 401
            if not current_user.is_active:
                return jsonify({"msg": "User is inactive."}), 401
            
            # Set current_user in Flask's g object for access in routes or other decorators
            g.current_user = current_user
            
        except jwt.ExpiredSignatureError:
            return jsonify({"msg": "Token has expired."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"msg": "Token is invalid."}), 401
        except Exception as e:
            current_app.logger.error(f"Token processing error: {e}")
            return jsonify({"msg": "Error processing token."}), 500
            
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    @token_required # Ensures token_required runs first and g.current_user is set
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user'):
             # This should ideally not be hit if @token_required is effective
            current_app.logger.error("g.current_user not set before admin_required check.")
            return jsonify(message="Authentication context not found."), 500 # Server error

        if g.current_user.role != 'admin':
            return jsonify(message="Admin access required."), 403
        return f(*args, **kwargs)
    return decorated_function

def employee_required(f):
    @wraps(f)
    @token_required # Ensures token_required runs first and g.current_user is set
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user'):
            current_app.logger.error("g.current_user not set before employee_required check.")
            return jsonify(message="Authentication context not found."), 500

        # An employee can be an 'employee' or an 'admin' (admin can do employee tasks)
        if g.current_user.role not in ['employee', 'admin']:
            return jsonify(message="Employee or Admin access required."), 403
        return f(*args, **kwargs)
    return decorated_function
