from flask import Flask
from ..config import Config
from .extensions import db, migrate # Added migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db) # Initialize migrate

    # Register blueprints
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from .routes.employee_routes import employee_bp
    app.register_blueprint(employee_bp)

    from .routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp)

    # Register other blueprints, etc. here later

    return app
