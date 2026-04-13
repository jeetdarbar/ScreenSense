from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
import os

# Initialize extension
db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # SQLAlchemy 1.4+ requires 'postgresql://' instead of 'postgres://' which Render uses
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    else:
        # Fallback to local SQLite
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '..', 'sleep_app_v2.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'dev-secret-key' # Change for production

    app.config['JWT_SECRET_KEY'] = 'jwt-super-secret-key-change-for-prod'

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)

    # Import models to ensure they are registered with SQLAlchemy
    from . import models

    # Create tables within app context
    with app.app_context():
        db.create_all()
        
        # Seed fundamental App Categories if missing
        seed_data = [
            {"package": "com.instagram.android", "category": "Social Media", "name": "Instagram"},
            {"package": "com.facebook.katana", "category": "Social Media", "name": "Facebook"},
            {"package": "com.reddit.frontpage", "category": "Social Media", "name": "Reddit"},
            {"package": "com.snapchat.android", "category": "Social Media", "name": "Snapchat"},
            {"package": "com.twitter.android", "category": "Social Media", "name": "X/Twitter"},
            {"package": "com.zhiliaoapp.musically", "category": "Social Media", "name": "TikTok"}
        ]
        
        for app_data in seed_data:
            if not models.AppCategoryMap.query.filter_by(package_name=app_data["package"]).first():
                new_app = models.AppCategoryMap(
                    package_name=app_data["package"],
                    category=app_data["category"],
                    readable_name=app_data["name"]
                )
                db.session.add(new_app)
        db.session.commit()

    # Register Blueprints
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
