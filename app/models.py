# ==== AURA_V2/app/models.py ====
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
import json

user_client_association = db.Table('user_client',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('client_id', db.Integer, db.ForeignKey('client.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    ROLES = ['Admin', 'Gestor', 'Colaborador', 'Cliente']
    role = db.Column(db.String(64), nullable=False, default='Cliente')
    clients = db.relationship(
        'Client', secondary=user_client_association,
        back_populates='users', lazy='dynamic')
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)
    def is_role(self, role_name): return self.role == role_name
    def __repr__(self): return f'<User {self.username}>'

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    users = db.relationship(
        'User', secondary=user_client_association,
        back_populates='clients', lazy='dynamic')
    data_sources = db.relationship('DataSource', backref='client', lazy='dynamic', cascade="all, delete-orphan")
    def __repr__(self): return f'<Client {self.name}>'

class DataSource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    credentials_json = db.Column(db.Text, nullable=False)
    def set_credentials(self, data): self.credentials_json = json.dumps(data)
    def get_credentials(self): return json.loads(self.credentials_json)
    def __repr__(self): return f'<DataSource {self.platform} for Client {self.client.name}>'