# ==== AURA_V2/app/main/routes.py ====

from flask import render_template, redirect, url_for, session, flash
from flask_login import login_required, current_user
from . import main
from .forms import AnalyticsStudioForm
from app.models import Client, DataSource
from app.zabbix_api import ZabbixService, ZabbixServiceError

@main.route('/')
@main.route('/index')
@login_required
def index():
    """Dashboard principal que lista os clientes do utilizador."""
    # Se for Admin, vê todos. Se não, vê apenas os clientes associados.
    clients = Client.query.all() if current_user.is_role('Admin') else current_user.clients.all()
    return render_template('main/index.html', title='Dashboard', clients=clients)

@main.route('/client/<int:client_id>')
@login_required
def client_dashboard(client_id):
    """Dashboard de um cliente específico."""
    client = Client.query.get_or_404(client_id)
    # TODO: Adicionar verificação de permissão para Gestores e Colaboradores
    
    # Guarda o cliente selecionado na sessão para uso posterior
    session['selected_client_id'] = client.id
    return render_template('main/client_dashboard.html', title=f"Dashboard {client.name}", client=client)

@main.route('/analytics-studio')
@login_required
def analytics_studio():
    """Página principal para a criação de relatórios."""
    client_id = session.get('selected_client_id')
    if not client_id:
        flash('Por favor, selecione um cliente primeiro.', 'warning')
        return redirect(url_for('main.index'))
    
    client = Client.query.get_or_404(client_id)
    form = AnalyticsStudioForm()

    try:
        # Tenta carregar os grupos de hosts do Zabbix para preencher o formulário
        zabbix_ds = client.data_sources.filter(DataSource.platform.ilike('Zabbix')).first()
        if zabbix_ds:
            zabbix = ZabbixService(zabbix_ds)
            host_groups = zabbix.get('hostgroup.get', {'output': ['groupid', 'name']})
            # Ordena os grupos por nome para uma melhor experiência
            sorted_groups = sorted(host_groups, key=lambda x: x['name'])
            form.host_groups.choices = [(g['groupid'], g['name']) for g in sorted_groups]
        else:
            flash("Nenhuma Fonte de Dados Zabbix encontrada para carregar os grupos de hosts.", 'warning')
    except ZabbixServiceError as e:
        flash(f'Erro ao carregar grupos de hosts do Zabbix: {e}', 'danger')
        form.host_groups.choices = []

    return render_template('main/analytics_studio.html', title='Analytics Studio', form=form, client=client)