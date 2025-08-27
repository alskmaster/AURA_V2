# ==== AURA_V2/app/__init__.py ====
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça o login para acessar esta página.'
login_manager.login_message_category = 'info'

def create_app(config_name='default'):
    """Fábrica da aplicação que cria e configura a instância do Flask."""
    app = Flask(__name__, instance_relative_config=True)
    
    # Garante que a pasta 'instance' exista
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Registro dos Blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    return app

from . import models

@login_manager.user_loader
def load_user(user_id):
    """Recarrega o objeto do usuário a partir do ID armazenado na sessão."""
    return models.User.query.get(int(user_id))