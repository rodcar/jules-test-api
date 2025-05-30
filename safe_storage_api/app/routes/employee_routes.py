from flask import Blueprint, request, jsonify, current_app, g # Added g
from werkzeug.security import generate_password_hash
from ..models import User, Client, Employee, StorageRental, StorageUnit, StorageUnitType
from ..extensions import db
from ..utils.decorators import employee_required # Added decorator
import datetime

employee_bp = Blueprint('employee', __name__, url_prefix='/api/employee')

# Authentication Placeholder and get_current_employee_id() removed.

# --- Client Management Endpoints ---

@employee_bp.route('/clients', methods=['POST'])
@employee_required # Added decorator
def register_client():
    # g.current_user is available (User object)
    # g.current_user.employee is available (Employee object associated with the User)
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON payload"}), 400

    required_fields = ['username', 'password', 'full_name', 'email']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({"msg": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    username = data['username']
    password = data['password']
    full_name = data['full_name']
    email = data['email']
    phone_number = data.get('phone_number')
    address = data.get('address')

    if User.query.filter_by(username=username).first():
        return jsonify({"msg": f"Username '{username}' already exists"}), 409
    # It's possible a user exists but not as a client yet.
    # For simplicity, current model for Client has its own email field.
    # Ensure email in Client table is unique.
    if Client.query.filter_by(email=email).first():
        return jsonify({"msg": f"Email '{email}' already registered to a client"}), 409

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    new_user = User(
        username=username,
        password_hash=hashed_password,
        role='client',
        is_active=True
    )
    db.session.add(new_user)
    
    try:
        db.session.flush() # Get new_user.id
        new_client = Client(
            user_id=new_user.id,
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            address=address
        )
        db.session.add(new_client)
        db.session.commit()

        client_data = {
            "id": new_client.id,
            "user_id": new_client.user_id,
            "full_name": new_client.full_name,
            "email": new_client.email,
            "phone_number": new_client.phone_number,
            "address": new_client.address,
            "username": new_user.username
        }
        return jsonify({"msg": "Client registered successfully", "client": client_data}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error registering client: {e}")
        return jsonify({"msg": "Internal server error during client registration"}), 500

@employee_bp.route('/clients/<int:client_id>', methods=['PUT'])
@employee_required # Added decorator
def update_client(client_id):
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"msg": "Client not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON payload"}), 400

    # Update client fields
    if 'full_name' in data:
        client.full_name = data['full_name']
    if 'email' in data:
        # Check for email uniqueness if it's being changed
        new_email = data['email']
        if new_email != client.email and Client.query.filter_by(email=new_email).first():
            return jsonify({"msg": f"Email '{new_email}' already in use"}), 409
        client.email = new_email
    if 'phone_number' in data:
        client.phone_number = data['phone_number']
    if 'address' in data:
        client.address = data['address']
    
    # If username or other User-specific fields were updatable, handle here
    # e.g., client.user.username = data['username'] if 'username' in data etc.

    try:
        db.session.commit()
        client_data = {
            "id": client.id,
            "user_id": client.user_id,
            "full_name": client.full_name,
            "email": client.email,
            "phone_number": client.phone_number,
            "address": client.address,
            "username": client.user.username # Assuming client.user relationship is loaded
        }
        return jsonify({"msg": "Client updated successfully", "client": client_data}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating client: {e}")
        return jsonify({"msg": "Internal server error during client update"}), 500

@employee_bp.route('/clients', methods=['GET'])
@employee_required # Added decorator
def list_clients():
    clients = Client.query.all()
    clients_data = []
    for client in clients:
        clients_data.append({
            "id": client.id,
            "user_id": client.user_id,
            "full_name": client.full_name,
            "email": client.email,
            "phone_number": client.phone_number,
            "address": client.address,
            "username": client.user.username # Assuming client.user relationship is loaded
        })
    return jsonify(clients_data), 200

# --- Rental Management Endpoints ---

@employee_bp.route('/rentals', methods=['POST'])
@employee_required # Added decorator
def register_rental():
    # g.current_user is the User instance of the authenticated employee (or admin)
    # g.current_user.employee is the associated Employee instance
    if not g.current_user.employee:
        # This case implies an admin user without an employee profile is trying this.
        # Or a client user, which @employee_required should prevent.
        # If admin should be able to register rentals without an employee profile,
        # this logic or the decorator needs adjustment. For now, assume employee profile is needed.
        return jsonify({"msg": "User does not have an associated employee profile."}), 403

    employee_id = g.current_user.employee.id # Get ID from the User's employee relationship

    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON payload"}), 400

    required_fields = ['client_id', 'storage_unit_id', 'end_date']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({"msg": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    client_id = data['client_id']
    storage_unit_id = data['storage_unit_id']
    end_date_str = data['end_date'] # Expecting YYYY-MM-DD format

    try:
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"msg": "Invalid end_date format. Use YYYY-MM-DD."}), 400

    price_at_rental = data.get('price_at_rental')
    is_paid = data.get('is_paid', False)

    client = Client.query.get(client_id)
    if not client:
        return jsonify({"msg": "Client not found"}), 404

    storage_unit = StorageUnit.query.get(storage_unit_id)
    if not storage_unit:
        return jsonify({"msg": "Storage unit not found"}), 404
    
    if not storage_unit.is_available:
        return jsonify({"msg": "Storage unit is not available"}), 409

    if price_at_rental is None:
        if storage_unit.type: # type is the relationship to StorageUnitType
            price_at_rental = storage_unit.type.price_per_month
        else: # Should not happen if data is consistent
            return jsonify({"msg": "Cannot determine price for storage unit type"}), 500
    
    start_date = datetime.date.today() # Use date object if end_date is also date

    new_rental = StorageRental(
        client_id=client_id,
        storage_unit_id=storage_unit_id,
        employee_id=employee_id, # From g.current_user.employee.id
        start_date=start_date,
        end_date=end_date,
        price_at_rental=price_at_rental,
        is_paid=is_paid,
        payment_date=datetime.datetime.utcnow() if is_paid else None
    )
    
    storage_unit.is_available = False # Mark unit as unavailable

    try:
        db.session.add(new_rental)
        db.session.add(storage_unit) # To update its availability
        db.session.commit()

        rental_data = {
            "id": new_rental.id,
            "client_id": new_rental.client_id,
            "storage_unit_id": new_rental.storage_unit_id,
            "employee_id": new_rental.employee_id,
            "start_date": new_rental.start_date.isoformat(),
            "end_date": new_rental.end_date.isoformat(),
            "price_at_rental": str(new_rental.price_at_rental), # Numeric to string
            "is_paid": new_rental.is_paid,
            "payment_date": new_rental.payment_date.isoformat() if new_rental.payment_date else None
        }
        return jsonify({"msg": "Storage rental registered successfully", "rental": rental_data}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error registering rental: {e}")
        return jsonify({"msg": "Internal server error during rental registration"}), 500

@employee_bp.route('/rentals', methods=['GET'])
@employee_required # Added decorator
def list_rentals():
    rentals = StorageRental.query.all()
    rentals_data = []
    for rental in rentals:
        rentals_data.append({
            "id": rental.id,
            "client_id": rental.client_id,
            "client_full_name": rental.client.full_name, # Assuming relationship is loaded
            "storage_unit_id": rental.storage_unit_id,
            "storage_unit_identifier": rental.storage_unit.unit_identifier, # Assuming relationship
            "employee_id": rental.employee_id,
            "employee_full_name": rental.employee.full_name, # Assuming relationship
            "start_date": rental.start_date.isoformat(),
            "end_date": rental.end_date.isoformat(),
            "price_at_rental": str(rental.price_at_rental),
            "is_paid": rental.is_paid,
            "payment_date": rental.payment_date.isoformat() if rental.payment_date else None
        })
    return jsonify(rentals_data), 200
