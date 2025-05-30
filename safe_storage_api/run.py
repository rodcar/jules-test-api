import click
from werkzeug.security import generate_password_hash
from .app import create_app, db # Changed to relative import
# Import all models to ensure they are registered with SQLAlchemy before migration/seeding
from .app.models import User, Client, Employee, StorageLocation, StorageUnitType, StorageUnit, Product, StorageRental # Changed to relative import

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'app': app, 
        'db': db, 
        'User': User,
        'Client': Client,
        'Employee': Employee,
        'StorageLocation': StorageLocation,
        'StorageUnitType': StorageUnitType,
        'StorageUnit': StorageUnit,
        'Product': Product,
        'StorageRental': StorageRental
    }

@app.cli.command("seed_db")
@click.option('--username', default='admin', help='Admin username')
@click.option('--password', default='adminpass', help='Admin password')
@click.option('--role', default='admin', help='User role')
def seed_db_command(username, password, role):
    """Creates an initial user (admin by default)."""
    user = User.query.filter_by(username=username).first()
    if user:
        print(f"User {username} already exists.")
        # Optionally, update if exists and new role or other params are different
        # For now, just return
        return

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(username=username, password_hash=hashed_password, role=role, is_active=True)
    
    db.session.add(new_user)
    
    # If the role is 'client' or 'employee', we might want to create associated entries.
    # For simplicity, the current task focuses on an admin user.
    # This can be expanded later.
    if role == 'client':
        # Placeholder: Create a Client entry if necessary, or prompt for more info
        # For now, this example assumes Client requires more details not provided here
        pass
    elif role == 'employee':
        # Placeholder: Create an Employee entry
        pass
        
    db.session.commit()
    print(f"User {username} with role {role} created successfully.")

if __name__ == '__main__':
    app.run()
