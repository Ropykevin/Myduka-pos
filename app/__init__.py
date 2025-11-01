from flask import Flask
from flask_login import LoginManager
from config import Config

# Import db from models to avoid circular imports
from app.models import db

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    from app import models
    from app.routes import register_routes
    
    register_routes(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))
    
    return app

