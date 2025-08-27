# ==== AURA_V2/app/admin/forms.py ====

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional
from app.models import User, Client, DataSource

class UserForm(FlaskForm):
    """Formulário para criar e editar um Utilizador."""
    username = StringField('Nome de Utilizador', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Papel', choices=User.ROLES, validators=[DataRequired()])
    password = PasswordField('Senha', validators=[Optional()])
    password2 = PasswordField(
        'Repita a Senha', 
        validators=[Optional(), EqualTo('password', message='As senhas devem ser iguais.')]
    )
    submit = SubmitField('Salvar Utilizador')

    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user:
                raise ValidationError('Este nome de utilizador já está em uso. Por favor, escolha outro.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=self.email.data).first()
            if user:
                raise ValidationError('Este email já está registado. Por favor, escolha outro.')


class ClientForm(FlaskForm):
    """Formulário para criar e editar um Cliente."""
    name = StringField('Nome do Cliente', validators=[DataRequired()])
    submit = SubmitField('Salvar Cliente')

    def __init__(self, original_name=None, *args, **kwargs):
        super(ClientForm, self).__init__(*args, **kwargs)
        self.original_name = original_name

    def validate_name(self, name):
        if name.data != self.original_name:
            client = Client.query.filter_by(name=name.data).first()
            if client:
                raise ValidationError('Este nome de cliente já está em uso.')


class DataSourceForm(FlaskForm):
    """Formulário para criar/editar uma Fonte de Dados (Zabbix, Softdesk, etc.)."""
    platform = SelectField('Plataforma', choices=[
        ('Zabbix', 'Zabbix'),
        ('Softdesk', 'Softdesk')
    ], validators=[DataRequired()])
    
    credentials_json = TextAreaField(
        'Credenciais (formato JSON)',
        validators=[DataRequired()],
        render_kw={'rows': 8}
    )
    submit = SubmitField('Salvar Fonte de Dados')