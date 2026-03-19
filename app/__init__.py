from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Initialize extension
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '..', 'sleep_app_v2.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'dev-secret-key' # Change for production

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'

    # Import models to ensure they are registered with SQLAlchemy
    from . import models

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    # Create tables within app context
    with app.app_context():
        db.create_all()

    # Register Blueprints
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
