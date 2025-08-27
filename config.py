# ==== AURA_V2/config.py ====
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'voce-precisa-mudar-esta-chave-secreta'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_FILE = 'app.log'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'aura_dev.db')

config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig
}