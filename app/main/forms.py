# ==== AURA_V2/app/main/forms.py ====

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired

class AnalyticsStudioForm(FlaskForm):
    """Formulário para configurar e gerar um relatório."""
    report_name = StringField(
        'Nome do Relatório', 
        validators=[DataRequired()], 
        default="Relatório de Performance Mensal"
    )
    
    # Este campo será preenchido dinamicamente via API
    host_groups = SelectMultipleField('Grupos de Hosts', choices=[], coerce=str)
    
    # Este campo será preenchido via JavaScript
    hosts = SelectMultipleField('Hosts', choices=[], coerce=str)

    # Campos para o período 
    start_date = StringField('Data de Início', validators=[DataRequired()])
    end_date = StringField('Data de Fim', validators=[DataRequired()])

    # Campo oculto para armazenar a ordem dos módulos
    report_layout_order = HiddenField()

    submit = SubmitField('Gerar Relatório')