# ==== AURA_V2/app/main/routes.py (VERSÃO FINAL E CORRIGIDA) ====

from flask import render_template, redirect, url_for, session, flash, jsonify, request, current_app, send_file
from flask_login import login_required, current_user
import os # Importar o módulo 'os' para manipulação de caminhos
import json

from . import main
from .forms import AnalyticsStudioForm
from app.models import Client, DataSource
from app.zabbix_api import ZabbixService, ZabbixServiceError
from app.collectors import AVAILABLE_COLLECTORS
from app.report_generator import ReportGenerator

@main.route('/')
@main.route('/index')
@login_required
def index():
    clients = Client.query.all() if current_user.is_role('Admin') else current_user.clients.all()
    return render_template('main/index.html', title='Dashboard', clients=clients)

@main.route('/client/<int:client_id>')
@login_required
def client_dashboard(client_id):
    client = Client.query.get_or_404(client_id)
    session['selected_client_id'] = client.id
    return render_template('main/client_dashboard.html', title=f"Dashboard {client.name}", client=client)

@main.route('/analytics-studio')
@login_required
def analytics_studio():
    client_id = session.get('selected_client_id')
    if not client_id:
        flash('Por favor, selecione um cliente primeiro.', 'warning')
        return redirect(url_for('main.index'))
    
    client = Client.query.get_or_404(client_id)
    form = AnalyticsStudioForm()
    try:
        zabbix_ds = client.data_sources.filter(DataSource.platform.ilike('Zabbix')).first()
        if zabbix_ds:
            zabbix = ZabbixService(zabbix_ds)
            host_groups = zabbix.get('hostgroup.get', {'output': ['groupid', 'name']})
            sorted_groups = sorted(host_groups, key=lambda x: x['name'])
            form.host_groups.choices = [(g['groupid'], g['name']) for g in sorted_groups]
        else:
            flash("Nenhuma Fonte de Dados Zabbix encontrada para carregar os grupos de hosts.", 'warning')
    except ZabbixServiceError as e:
        flash(f'Erro ao carregar grupos de hosts do Zabbix: {e}', 'danger')
        form.host_groups.choices = []
    return render_template('main/analytics_studio.html', title='Analytics Studio', form=form, client=client)

@main.route('/generate-report', methods=['POST'])
@login_required
def generate_report():
    client_id = session.get('selected_client_id')
    client = Client.query.get_or_404(client_id)
    
    report_config = {
        'report_name': request.form.get('report_name'),
        'modules': json.loads(request.form.get('report_layout_order', '[]')),
        'hosts': request.form.getlist('hosts'),
        'start_date': request.form.get('start_date'),
        'end_date': request.form.get('end_date'),
    }

    if not report_config['modules']:
        flash('Nenhum módulo foi adicionado ao layout do relatório.', 'warning')
        return redirect(url_for('main.analytics_studio'))

    try:
        generator = ReportGenerator(client, report_config)
        relative_pdf_path = generator.generate()
        
        if relative_pdf_path:
            # --- CORREÇÃO APLICADA AQUI ---
            # Convertemos o caminho relativo para um caminho absoluto
            absolute_pdf_path = os.path.abspath(relative_pdf_path)
            
            # Enviamos o caminho absoluto para o Flask, garantindo que ele o encontre
            return send_file(absolute_pdf_path, as_attachment=True)
        else:
            flash('Não foi possível gerar o relatório. Verifique se há dados para os parâmetros selecionados.', 'warning')
            return redirect(url_for('main.analytics_studio'))
            
    except Exception as e:
        flash(f'Ocorreu um erro inesperado ao gerar o relatório: {e}', 'danger')
        current_app.logger.error(f"Erro na geração do relatório: {e}", exc_info=True)
        return redirect(url_for('main.analytics_studio'))

# --- APIs (removi o debug para a versão final) ---
@main.route('/api/get_all_modules')
@login_required
def get_all_modules():
    all_modules = [{'key': key, 'name': data['name']} for key, data in AVAILABLE_COLLECTORS.items()]
    return jsonify({'all_modules': all_modules})

@main.route('/api/get_hosts/<string:group_ids>')
@login_required
def get_hosts(group_ids):
    client_id = session.get('selected_client_id')
    client = Client.query.get_or_404(client_id)
    try:
        zabbix_ds = client.data_sources.filter(DataSource.platform.ilike('Zabbix')).first()
        if not zabbix_ds:
            return jsonify({'error': 'Fonte de dados Zabbix não configurada.'}), 500
            
        zabbix = ZabbixService(zabbix_ds)
        hosts = zabbix.get('host.get', {
            'output': ['hostid', 'name'],
            'groupids': group_ids.split(','),
            'sortfield': 'name'
        })
        return jsonify([{'id': h['hostid'], 'name': h['name']} for h in hosts])
    except ZabbixServiceError as e:
        return jsonify({'error': str(e)}), 500

@main.route('/api/validate_modules', methods=['POST'])
@login_required
def validate_modules():
    client_id = session.get('selected_client_id')
    client = Client.query.get_or_404(client_id)
    host_ids = request.json.get('host_ids', [])
    if not host_ids: return jsonify({'supported_modules': []})
    
    platform_services, supported_modules = {}, []
    try:
        for key, data in AVAILABLE_COLLECTORS.items():
            collector_class = data['class']
            required_platform = collector_class.platform
            if required_platform not in platform_services:
                ds = client.data_sources.filter(DataSource.platform.ilike(required_platform)).first()
                if ds:
                    if required_platform.lower() == 'zabbix':
                        platform_services[required_platform] = ZabbixService(ds)
            
            if required_platform in platform_services:
                service_instance = platform_services[required_platform]
                if collector_class.is_supported(service_instance, host_ids):
                    supported_modules.append({'key': key, 'name': data['name']})
        
        return jsonify({'supported_modules': supported_modules})
    except Exception as e:
        current_app.logger.error(f"Erro ao validar módulos: {e}", exc_info=True)
        return jsonify({'error': f'Erro ao validar módulos: {e}'}), 500