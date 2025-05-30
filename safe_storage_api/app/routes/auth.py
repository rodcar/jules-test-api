import jwt
import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from ..models import User, Employee # Assuming models.py is in the parent directory of routes
from ..extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"msg": "Missing username or password"}), 400

    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"msg": "Bad username or password"}), 401

    # Identity for the token
    identity = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1) # Token expires in 1 hour
    }
    
    try:
        token = jwt.encode(
            identity,
            current_app.config['JWT_SECRET_KEY'],
            algorithm="HS256"
        )
        return jsonify(access_token=token)
    except Exception as e:
        current_app.logger.error(f"Error encoding JWT: {e}")
        return jsonify({"msg": "Internal server error creating token"}), 500

from ..utils.decorators import admin_required # Added decorator

@auth_bp.route('/register_employee', methods=['POST'])
@admin_required # Applied decorator
def register_employee():
    # Admin check is now handled by @admin_required
    # g.current_user is available if needed for logging or context, but not strictly for this registration logic by another admin.
    
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON payload"}), 400

    username = data.get('username')
    password = data.get('password')
    full_name = data.get('full_name')
    employee_id_number = data.get('employee_id_number')

    if not all([username, password, full_name, employee_id_number]):
        return jsonify({"msg": "Missing required fields: username, password, full_name, employee_id_number"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"msg": f"Username '{username}' already exists"}), 409 # 409 Conflict

    if Employee.query.filter_by(employee_id_number=employee_id_number).first():
        return jsonify({"msg": f"Employee ID number '{employee_id_number}' already exists"}), 409

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    new_user = User(
        username=username,
        password_hash=hashed_password,
        role='employee',
        is_active=True
    )
    db.session.add(new_user)
    
    # We need to flush to get the new_user.id if it's an autoincrement PK
    # before creating the Employee record that depends on it.
    try:
        db.session.flush() # Get new_user.id

        new_employee = Employee(
            user_id=new_user.id,
            full_name=full_name,
            employee_id_number=employee_id_number
        )
        db.session.add(new_employee)
        db.session.commit()
        
        # Exclude password_hash from response
        user_data = {
            "id": new_user.id,
            "username": new_user.username,
            "role": new_user.role,
            "is_active": new_user.is_active
        }
        employee_data = {
            "id": new_employee.id,
            "user_id": new_employee.user_id,
            "full_name": new_employee.full_name,
            "employee_id_number": new_employee.employee_id_number
        }
        
        return jsonify({
            "msg": "Employee registered successfully", 
            "user": user_data,
            "employee": employee_data
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error registering employee: {e}")
        return jsonify({"msg": "Internal server error during registration"}), 500
