import os
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-fallback-key-change-in-prod")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Setup User Loader
    with app.app_context():
        from app.models import User
        
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(user_id)

    # Register Blueprints
    from app.routes.trips import trips_bp
    from app.routes.auth import auth_bp
    from app.routes.cars import cars_bp
    from app.routes.sites import sites_bp
    from app.routes.soldiers import soldiers_bp
    
    app.register_blueprint(trips_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cars_bp)
    app.register_blueprint(sites_bp)
    app.register_blueprint(soldiers_bp)

    @app.route('/')
    def index():
        return redirect(url_for('trips.list_trips'))

    with app.app_context():
        db.create_all()

    return app