import os

from flask import Flask

from .extensions import db, login_manager, migrate, csrf


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Ensure writable directories exist (works for both dev and frozen modes)
    from config import DATA_DIR
    os.makedirs(os.path.join(DATA_DIR, 'instance'), exist_ok=True)
    os.makedirs(app.config['QR_CODES_DIR'], exist_ok=True)
    os.makedirs(app.config['CERTIFICATES_DIR'], exist_ok=True)
    os.makedirs(app.config['STUDENT_PHOTOS_DIR'], exist_ok=True)
    os.makedirs(app.config['PROJECT_MEDIA_DIR'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # User loader for Flask-Login
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Serve user-generated files (QR codes, certificates) from the data dir.
    # In dev mode STATIC_DIR points inside the project; when frozen it points
    # to %LOCALAPPDATA%/ZHub/data.  Either way, this route makes them
    # accessible at /data/<path> in templates.
    from flask import send_from_directory

    @app.route('/data/<path:filename>')
    def serve_data_file(filename):
        return send_from_directory(app.config['STATIC_DIR'], filename)

    # Register blueprints
    from .auth import auth_bp
    from .admin import admin_bp
    from .students import students_bp
    from .instructors import instructors_bp
    from .courses import courses_bp
    from .payments import payments_bp
    from .attendance import attendance_bp
    from .certificates import certificates_bp
    from .qr import qr_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(instructors_bp, url_prefix='/instructors')
    app.register_blueprint(courses_bp, url_prefix='/courses')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(certificates_bp, url_prefix='/certificates')
    app.register_blueprint(qr_bp, url_prefix='/qr')

    # Create tables and seed default admin
    with app.app_context():
        db.create_all()
        _seed_admin()

    return app


def _seed_admin():
    """Create a default admin account if none exists."""
    from .models import User

    admin = User.query.filter_by(role='admin').first()
    if admin is None:
        admin = User(
            email='admin@zhub.com',
            first_name='Admin',
            last_name='User',
            role='admin',
            is_active=True,
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
