from flask import Blueprint, request, jsonify, current_app, g # Added g
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import (
    User, Client, Employee, 
    StorageLocation, StorageUnitType, StorageUnit, 
    Product, StorageRental
)
from ..extensions import db
from ..utils.decorators import admin_required # Added decorator
import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Authentication Placeholder ensure_admin_access() and check_auth() removed.
# @admin_required decorator will handle authentication and authorization.

# --- Manage Storage Rentals ---
@admin_bp.route('/rentals', methods=['GET'])
@admin_required # Added decorator
def list_all_rentals():
    # g.current_user is available (admin User object)
    rentals = StorageRental.query.all()
    return jsonify([{
        "id": r.id, "client_id": r.client_id, "client_full_name": r.client.full_name,
        "storage_unit_id": r.storage_unit_id, "storage_unit_identifier": r.storage_unit.unit_identifier,
        "employee_id": r.employee_id, "employee_full_name": r.employee.full_name,
        "start_date": r.start_date.isoformat(), "end_date": r.end_date.isoformat(),
        "price_at_rental": str(r.price_at_rental), "is_paid": r.is_paid,
        "payment_date": r.payment_date.isoformat() if r.payment_date else None
    } for r in rentals]), 200

@admin_bp.route('/rentals', methods=['POST'])
@admin_required # Added decorator
def admin_create_rental():
    data = request.get_json()
    required = ['client_id', 'storage_unit_id', 'employee_id', 'end_date']
    if not all(k in data for k in required):
        return jsonify({"msg": f"Missing fields. Required: {', '.join(required)}"}), 400

    client = Client.query.get(data['client_id'])
    unit = StorageUnit.query.get(data['storage_unit_id'])
    employee = Employee.query.get(data['employee_id'])

    if not client: return jsonify({"msg": "Client not found"}), 404
    if not unit: return jsonify({"msg": "Storage unit not found"}), 404
    if not unit.is_available: return jsonify({"msg": "Storage unit not available"}), 409
    if not employee: return jsonify({"msg": "Employee not found"}), 404

    try:
        end_date = datetime.datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"msg": "Invalid end_date format. Use YYYY-MM-DD."}), 400
    
    price = data.get('price_at_rental', unit.type.price_per_month)

    rental = StorageRental(
        client_id=data['client_id'], storage_unit_id=data['storage_unit_id'],
        employee_id=data['employee_id'], start_date=datetime.date.today(),
        end_date=end_date, price_at_rental=price,
        is_paid=data.get('is_paid', False),
        payment_date=datetime.datetime.utcnow() if data.get('is_paid') else None
    )
    unit.is_available = False
    db.session.add(rental)
    db.session.add(unit)
    try:
        db.session.commit()
        return jsonify({"msg": "Rental created", "id": rental.id}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Admin create rental error: {e}")
        return jsonify({"msg": "Could not create rental"}), 500


@admin_bp.route('/rentals/<int:rental_id>', methods=['PUT'])
@admin_required # Added decorator
def admin_update_rental(rental_id):
    rental = StorageRental.query.get(rental_id)
    if not rental: return jsonify({"msg": "Rental not found"}), 404
    data = request.get_json()
    
    if 'end_date' in data:
        try:
            rental.end_date = datetime.datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"msg": "Invalid end_date format. Use YYYY-MM-DD."}), 400
    if 'is_paid' in data:
        rental.is_paid = data['is_paid']
        if data['is_paid'] and not rental.payment_date:
            rental.payment_date = datetime.datetime.utcnow()
        elif not data['is_paid']:
            rental.payment_date = None # Clear payment date if marked unpaid
    if 'price_at_rental' in data:
        rental.price_at_rental = data['price_at_rental']
    # Potentially allow changing client, unit, employee - but this is complex.
    # For now, focus on state changes like payment and end_date.

    try:
        db.session.commit()
        return jsonify({"msg": "Rental updated", "id": rental.id}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Admin update rental error: {e}")
        return jsonify({"msg": "Could not update rental"}), 500

@admin_bp.route('/rentals/<int:rental_id>', methods=['DELETE'])
@admin_required # Added decorator
def admin_delete_rental(rental_id):
    rental = StorageRental.query.get(rental_id)
    if not rental: return jsonify({"msg": "Rental not found"}), 404
    
    # Mark unit as available again
    if rental.storage_unit:
        rental.storage_unit.is_available = True
        db.session.add(rental.storage_unit)

    db.session.delete(rental)
    try:
        db.session.commit()
        return jsonify({"msg": "Rental deleted"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Admin delete rental error: {e}")
        return jsonify({"msg": "Could not delete rental"}), 500

# --- Manage Employees ---
@admin_bp.route('/employees', methods=['GET'])
@admin_required # Added decorator
def list_all_employees():
    employees = Employee.query.join(User, Employee.user_id == User.id).all()
    return jsonify([{
        "user_id": emp.user_id, "employee_db_id": emp.id, "username": emp.user.username,
        "full_name": emp.full_name, "employee_id_number": emp.employee_id_number,
        "is_active": emp.user.is_active, "role": emp.user.role
    } for emp in employees]), 200

@admin_bp.route('/employees', methods=['POST'])
@admin_required # Added decorator
def admin_create_employee():
    data = request.get_json()
    required = ['username', 'password', 'full_name', 'employee_id_number']
    if not all(k in data for k in required):
        return jsonify({"msg": f"Missing fields. Required: {', '.join(required)}"}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "Username already exists"}), 409
    if Employee.query.filter_by(employee_id_number=data['employee_id_number']).first():
        return jsonify({"msg": "Employee ID number already exists"}), 409

    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    user = User(username=data['username'], password_hash=hashed_password, role='employee', is_active=True)
    db.session.add(user)
    try:
        db.session.flush() # Get user.id
        employee = Employee(user_id=user.id, full_name=data['full_name'], employee_id_number=data['employee_id_number'])
        db.session.add(employee)
        db.session.commit()
        return jsonify({
            "msg": "Employee created", "user_id": user.id, "employee_id_number": employee.employee_id_number
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Admin create employee error: {e}")
        return jsonify({"msg": "Could not create employee"}), 500

@admin_bp.route('/employees/<int:employee_user_id>', methods=['PUT'])
@admin_required # Added decorator
def admin_update_employee(employee_user_id):
    user = User.query.get(employee_user_id)
    if not user or user.role != 'employee':
        return jsonify({"msg": "Employee user not found"}), 404
    
    employee = Employee.query.filter_by(user_id=user.id).first()
    if not employee: # Should not happen if data is consistent
        return jsonify({"msg": "Employee record not found for user"}), 404

    data = request.get_json()
    if 'full_name' in data: employee.full_name = data['full_name']
    if 'employee_id_number' in data:
        new_eid = data['employee_id_number']
        if new_eid != employee.employee_id_number and Employee.query.filter_by(employee_id_number=new_eid).first():
            return jsonify({"msg": "Employee ID number already in use"}), 409
        employee.employee_id_number = new_eid
    if 'is_active' in data: user.is_active = data['is_active']
    # Add password change if needed, or username change (careful with uniqueness)
    
    try:
        db.session.commit()
        return jsonify({"msg": "Employee updated", "user_id": user.id}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Admin update employee error: {e}")
        return jsonify({"msg": "Could not update employee"}), 500

@admin_bp.route('/employees/<int:employee_user_id>', methods=['DELETE'])
@admin_required # Added decorator
def admin_delete_employee(employee_user_id):
    user = User.query.get(employee_user_id)
    if not user or user.role != 'employee':
        return jsonify({"msg": "Employee user not found"}), 404
    
    # Option 1: Mark as inactive (soft delete)
    # user.is_active = False 
    # db.session.commit()
    # return jsonify({"msg": "Employee marked as inactive"}), 200

    # Option 2: Hard delete (more complex due to FKs, e.g., rentals)
    # Check if employee has rentals, reassign or handle them
    if StorageRental.query.filter_by(employee_id=user.employee.id).first(): # user.employee is the backref
         return jsonify({"msg": "Cannot delete employee with active rentals. Please reassign rentals first or mark as inactive."}), 409
    
    employee_record = Employee.query.filter_by(user_id=user.id).first()
    if employee_record:
        db.session.delete(employee_record)
    db.session.delete(user) # Then delete user
    try:
        db.session.commit()
        return jsonify({"msg": "Employee deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Admin delete employee error: {e}")
        return jsonify({"msg": "Could not delete employee. Check for dependencies."}), 500


# --- Manage Storage Units ---
@admin_bp.route('/storage_units', methods=['GET'])
@admin_required # Added decorator
def list_all_storage_units():
    units = StorageUnit.query.all()
    return jsonify([{
        "id": u.id, "unit_identifier": u.unit_identifier, 
        "location_id": u.location_id, "location_name": u.location.name,
        "type_id": u.type_id, "type_name": u.type.name, 
        "is_available": u.is_available
    } for u in units]), 200

@admin_bp.route('/storage_units', methods=['POST'])
@admin_required # Added decorator
def admin_create_storage_unit():
    data = request.get_json()
    required = ['unit_identifier', 'location_id', 'type_id']
    if not all(k in data for k in required):
        return jsonify({"msg": f"Missing fields. Required: {', '.join(required)}"}), 400

    if StorageUnit.query.filter_by(unit_identifier=data['unit_identifier']).first():
        return jsonify({"msg": "Unit identifier already exists"}), 409
    if not StorageLocation.query.get(data['location_id']):
        return jsonify({"msg": "Storage location not found"}), 404
    if not StorageUnitType.query.get(data['type_id']):
        return jsonify({"msg": "Storage unit type not found"}), 404

    unit = StorageUnit(
        unit_identifier=data['unit_identifier'], location_id=data['location_id'],
        type_id=data['type_id'], is_available=data.get('is_available', True)
    )
    db.session.add(unit)
    try:
        db.session.commit()
        return jsonify({"msg": "Storage unit created", "id": unit.id}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Admin create storage unit error: {e}")
        return jsonify({"msg": "Could not create storage unit"}), 500

@admin_bp.route('/storage_units/<int:unit_id>', methods=['PUT'])
@admin_required # Added decorator
def admin_update_storage_unit(unit_id):
    unit = StorageUnit.query.get(unit_id)
    if not unit: return jsonify({"msg": "Storage unit not found"}), 404
    data = request.get_json()

    if 'unit_identifier' in data:
        new_id = data['unit_identifier']
        if new_id != unit.unit_identifier and StorageUnit.query.filter_by(unit_identifier=new_id).first():
            return jsonify({"msg": "Unit identifier already in use"}), 409
        unit.unit_identifier = new_id
    if 'location_id' in data:
        if not StorageLocation.query.get(data['location_id']): return jsonify({"msg": "Location not found"}), 404
        unit.location_id = data['location_id']
    if 'type_id' in data:
        if not StorageUnitType.query.get(data['type_id']): return jsonify({"msg": "Type not found"}), 404
        unit.type_id = data['type_id']
    if 'is_available' in data: unit.is_available = data['is_available']
    
    try:
        db.session.commit()
        return jsonify({"msg": "Storage unit updated", "id": unit.id}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Admin update storage unit error: {e}")
        return jsonify({"msg": "Could not update storage unit"}), 500

@admin_bp.route('/storage_units/<int:unit_id>', methods=['DELETE'])
@admin_required # Added decorator
def admin_delete_storage_unit(unit_id):
    unit = StorageUnit.query.get(unit_id)
    if not unit: return jsonify({"msg": "Storage unit not found"}), 404

    if StorageRental.query.filter_by(storage_unit_id=unit.id, end_date >= datetime.date.today()).first(): # Check active rentals
         return jsonify({"msg": "Cannot delete unit with active rentals. Please resolve rentals first."}), 409
    
    db.session.delete(unit)
    try:
        db.session.commit()
        return jsonify({"msg": "Storage unit deleted"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Admin delete storage unit error: {e}")
        return jsonify({"msg": "Could not delete storage unit. Check for dependencies."}), 500

# --- Manage Storage Unit Types ---
@admin_bp.route('/storage_unit_types', methods=['GET'])
@admin_required # Added decorator
def list_storage_unit_types():
    types = StorageUnitType.query.all()
    return jsonify([{
        "id": t.id, "name": t.name, "description": t.description,
        "size": t.size, "price_per_month": str(t.price_per_month)
    } for t in types]), 200

@admin_bp.route('/storage_unit_types', methods=['POST'])
@admin_required # Added decorator
def create_storage_unit_type():
    data = request.get_json()
    required = ['name', 'price_per_month']
    if not all(k in data for k in required):
        return jsonify({"msg": f"Missing fields. Required: {', '.join(required)}"}), 400
    if StorageUnitType.query.filter_by(name=data['name']).first():
        return jsonify({"msg": "Storage unit type name already exists"}), 409

    sut = StorageUnitType(
        name=data['name'], description=data.get('description'),
        size=data.get('size'), price_per_month=data['price_per_month']
    )
    db.session.add(sut)
    try:
        db.session.commit()
        return jsonify({"msg": "Storage unit type created", "id": sut.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Could not create storage unit type"}), 500

@admin_bp.route('/storage_unit_types/<int:type_id>', methods=['PUT'])
@admin_required # Added decorator
def update_storage_unit_type(type_id):
    sut = StorageUnitType.query.get(type_id)
    if not sut: return jsonify({"msg": "Storage unit type not found"}), 404
    data = request.get_json()
    if 'name' in data:
        new_name = data['name']
        if new_name != sut.name and StorageUnitType.query.filter_by(name=new_name).first():
            return jsonify({"msg": "Storage unit type name already exists"}), 409
        sut.name = new_name
    if 'description' in data: sut.description = data['description']
    if 'size' in data: sut.size = data['size']
    if 'price_per_month' in data: sut.price_per_month = data['price_per_month']
    try:
        db.session.commit()
        return jsonify({"msg": "Storage unit type updated", "id": sut.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Could not update storage unit type"}), 500

@admin_bp.route('/storage_unit_types/<int:type_id>', methods=['DELETE'])
@admin_required # Added decorator
def delete_storage_unit_type(type_id):
    sut = StorageUnitType.query.get(type_id)
    if not sut: return jsonify({"msg": "Storage unit type not found"}), 404
    if StorageUnit.query.filter_by(type_id=sut.id).first():
        return jsonify({"msg": "Cannot delete type with existing units. Reassign units first."}), 409
    db.session.delete(sut)
    try:
        db.session.commit()
        return jsonify({"msg": "Storage unit type deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Could not delete storage unit type"}), 500

# --- Manage Storage Locations ---
@admin_bp.route('/storage_locations', methods=['GET'])
@admin_required # Added decorator
def list_storage_locations():
    locations = StorageLocation.query.all()
    return jsonify([{"id": loc.id, "name": loc.name, "address": loc.address} for loc in locations]), 200

@admin_bp.route('/storage_locations', methods=['POST'])
@admin_required # Added decorator
def create_storage_location():
    data = request.get_json()
    if not all(k in data for k in ['name', 'address']):
        return jsonify({"msg": "Missing name or address"}), 400
    if StorageLocation.query.filter_by(name=data['name']).first():
        return jsonify({"msg": "Location name already exists"}), 409
    loc = StorageLocation(name=data['name'], address=data['address'])
    db.session.add(loc)
    try:
        db.session.commit()
        return jsonify({"msg": "Storage location created", "id": loc.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Could not create storage location"}), 500

@admin_bp.route('/storage_locations/<int:location_id>', methods=['PUT'])
@admin_required # Added decorator
def update_storage_location(location_id):
    loc = StorageLocation.query.get(location_id)
    if not loc: return jsonify({"msg": "Location not found"}), 404
    data = request.get_json()
    if 'name' in data:
        new_name = data['name']
        if new_name != loc.name and StorageLocation.query.filter_by(name=new_name).first():
            return jsonify({"msg": "Location name already exists"}), 409
        loc.name = new_name
    if 'address' in data: loc.address = data['address']
    try:
        db.session.commit()
        return jsonify({"msg": "Storage location updated", "id": loc.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Could not update storage location"}), 500

@admin_bp.route('/storage_locations/<int:location_id>', methods=['DELETE'])
@admin_required # Added decorator
def delete_storage_location(location_id):
    loc = StorageLocation.query.get(location_id)
    if not loc: return jsonify({"msg": "Location not found"}), 404
    if StorageUnit.query.filter_by(location_id=loc.id).first():
        return jsonify({"msg": "Cannot delete location with units. Reassign units first."}), 409
    db.session.delete(loc)
    try:
        db.session.commit()
        return jsonify({"msg": "Storage location deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Could not delete storage location"}), 500

# --- Manage Products ---
@admin_bp.route('/products', methods=['GET'])
@admin_required # Added decorator
def list_products():
    products = Product.query.all()
    return jsonify([{
        "id": p.id, "name": p.name, "description": p.description, "price": str(p.price)
    } for p in products]), 200

@admin_bp.route('/products', methods=['POST'])
@admin_required # Added decorator
def create_product():
    data = request.get_json()
    if not all(k in data for k in ['name', 'price']):
        return jsonify({"msg": "Missing name or price"}), 400
    if Product.query.filter_by(name=data['name']).first():
        return jsonify({"msg": "Product name already exists"}), 409
    prod = Product(name=data['name'], description=data.get('description'), price=data['price'])
    db.session.add(prod)
    try:
        db.session.commit()
        return jsonify({"msg": "Product created", "id": prod.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Could not create product"}), 500

@admin_bp.route('/products/<int:product_id>', methods=['PUT'])
@admin_required # Added decorator
def update_product(product_id):
    prod = Product.query.get(product_id)
    if not prod: return jsonify({"msg": "Product not found"}), 404
    data = request.get_json()
    if 'name' in data:
        new_name = data['name']
        if new_name != prod.name and Product.query.filter_by(name=new_name).first():
            return jsonify({"msg": "Product name already exists"}), 409
        prod.name = new_name
    if 'description' in data: prod.description = data['description']
    if 'price' in data: prod.price = data['price']
    try:
        db.session.commit()
        return jsonify({"msg": "Product updated", "id": prod.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Could not update product"}), 500

@admin_bp.route('/products/<int:product_id>', methods=['DELETE'])
@admin_required # Added decorator
def delete_product(product_id):
    prod = Product.query.get(product_id)
    if not prod: return jsonify({"msg": "Product not found"}), 404
    # Check for dependencies if products can be linked to other tables (e.g., in orders, rentals)
    # For now, direct delete:
    db.session.delete(prod)
    try:
        db.session.commit()
        return jsonify({"msg": "Product deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Could not delete product"}), 500
