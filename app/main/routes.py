# ==== AURA_V2/app/main/routes.py (VERSÃO FINAL FASE 3) ====

from flask import render_template, redirect, url_for, session, flash, jsonify, request, current_app, send_file
from flask_login import login_required, current_user
import os
import json

from . import main
from .forms import AnalyticsStudioForm
from app.models import Client, DataSource
from app.zabbix_api import ZabbixService, ZabbixServiceError
from app.collectors import AVAILABLE_COLLECTORS
from app.report_generator import ReportGenerator # Importe o gerador

# ... (as rotas index, client_dashboard, e analytics_studio permanecem as mesmas) ...
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

# --- NOVA ROTA PARA GERAR O RELATÓRIO ---
@main.route('/generate-report', methods=['POST'])
@login_required
def generate_report():
    client_id = session.get('selected_client_id')
    client = Client.query.get_or_404(client_id)
    
    # Extrai as configurações do formulário enviado
    report_config = {
        'report_name': request.form.get('report_name'),
        'modules': request.form.getlist('modules'), # Pega os checkboxes dos módulos
        'hosts': request.form.getlist('hosts'),
        'start_date': request.form.get('start_date'),
        'end_date': request.form.get('end_date'),
    }

    if not report_config['modules']:
        flash('Nenhum módulo foi selecionado para o relatório.', 'warning')
        return redirect(url_for('main.analytics_studio'))

    try:
        generator = ReportGenerator(client, report_config)
        pdf_path = generator.generate()
        
        if pdf_path:
            # Envia o ficheiro PDF gerado para o utilizador fazer o download
            return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))
        else:
            flash('Não foi possível gerar o relatório. Verifique se há dados para os parâmetros selecionados.', 'warning')
            return redirect(url_for('main.analytics_studio'))
            
    except Exception as e:
        flash(f'Ocorreu um erro inesperado ao gerar o relatório: {e}', 'danger')
        current_app.logger.error(f"Erro na geração do relatório: {e}", exc_info=True)
        return redirect(url_for('main.analytics_studio'))

# --- ROTAS DE API PARA O JAVASCRIPT ---

@main.route('/api/get_hosts/<string:group_ids>')
@login_required
def get_hosts(group_ids):
    print("\\n--- INICIANDO DEBUG: ROTA /api/get_hosts CHAMADA ---")
    try:
        client_id = session.get('selected_client_id')
        print(f"[DEBUG] ID do cliente na sessão: {client_id}")
        client = Client.query.get_or_404(client_id)
        print(f"[DEBUG] Cliente encontrado: {client.name}")
        
        print("[DEBUG] A procurar pela Fonte de Dados Zabbix...")
        zabbix_ds = client.data_sources.filter(DataSource.platform.ilike('Zabbix')).first()
        
        if not zabbix_ds:
            print("[DEBUG] ERRO: Nenhuma Fonte de Dados Zabbix encontrada para este cliente.")
            return jsonify({'error': 'Fonte de dados Zabbix não configurada.'}), 500
        
        print(f"[DEBUG] Fonte de Dados encontrada (ID: {zabbix_ds.id}). A tentar criar ZabbixService...")
        zabbix = ZabbixService(zabbix_ds)
        print("[DEBUG] ZabbixService criado com SUCESSO.")
        
        print(f"[DEBUG] A buscar hosts para os group_ids: {group_ids}")
        hosts = zabbix.get('host.get', {
            'output': ['hostid', 'name'],
            'groupids': group_ids.split(','),
            'sortfield': 'name'
        })
        print(f"[DEBUG] Hosts encontrados: {hosts}")
        print("--- FIM DO DEBUG ---")
        return jsonify([{'id': h['hostid'], 'name': h['name']} for h in hosts])
        
    except Exception as e:
        print(f"[DEBUG] ERRO CATASTRÓFICO NA ROTA get_hosts: {e}")
        # Loga o erro completo no terminal para nós
        current_app.logger.error(f"Erro na API get_hosts: {e}", exc_info=True)
        print("--- FIM DO DEBUG COM ERRO ---")
        return jsonify({'error': str(e)}), 500


@main.route('/api/validate_modules', methods=['POST'])
@login_required
def validate_modules():
    # ... (código existente, sem debug por enquanto) ...
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