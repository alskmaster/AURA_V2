# ==== AURA_V2/app/report_generator.py (VERSÃO COM CONTAGEM DE PÁGINAS) ====

import uuid
import os
from flask import current_app
from .zabbix_api import ZabbixService
from .charting import ChartingService
from .pdf_builder import PDFBuilderService
from .models import DataSource
from .collectors import AVAILABLE_COLLECTORS
from datetime import datetime

class ReportGenerator:
    """Orquestra a coleta de dados e a geração do relatório final em PDF."""
    def __init__(self, client, report_config):
        self.client = client
        self.config = report_config
        self.charting = ChartingService()
        self.pdf_builder = PDFBuilderService()
        self.platform_services = {}

        for ds in self.client.data_sources:
            platform_name = ds.platform.capitalize()
            if platform_name == 'Zabbix':
                try:
                    self.platform_services[platform_name] = ZabbixService(ds)
                except Exception as e:
                    current_app.logger.error(f"Falha ao inicializar serviço Zabbix para o cliente {self.client.name}: {e}")

    def generate(self):
        """Executa um processo de dois passos para gerar o relatório com contagem de páginas correta."""
        collected_data = []
        has_data = False

        # --- Preparar contexto global inicial ---
        start_date_str = self.config.get('start_date')
        end_date_str = self.config.get('end_date')
        global_context = {
            'report_name': self.config.get('report_name', 'Relatório de Análise'),
            'client_name': self.client.name,
            'start_date': datetime.strptime(start_date_str, '%Y-%m-%d').strftime('%d/%m/%Y') if start_date_str else 'N/D',
            'end_date': datetime.strptime(end_date_str, '%Y-%m-%d').strftime('%d/%m/%Y') if end_date_str else 'N/D',
        }
        print(f"[DEBUG] ReportGenerator: Contexto global inicial criado: {global_context}")

        # --- FASE 1: Coleta de Dados ---
        # A coleta de dados, que é a parte mais demorada, acontece apenas uma vez.
        print("[DEBUG] ReportGenerator: Iniciando FASE 1 - Coleta de Dados.")
        for module_instance in self.config.get('modules', []):
            module_key = module_instance.get('type')
            if module_key in AVAILABLE_COLLECTORS:
                CollectorClass = AVAILABLE_COLLECTORS[module_key]['class']
                platform_service = self.platform_services.get(CollectorClass.platform)
                if platform_service:
                    collector = CollectorClass(platform_service, self.charting, self.config)
                    module_context = collector.collect(instance_config=module_instance)
                    if module_context:
                        has_data = True
                        # Guarda os dados coletados e a configuração para a fase de renderização
                        collected_data.append({
                            'key': module_key,
                            'context': module_context,
                            'instance': module_instance
                        })
        
        if not has_data:
            return None

        # --- FASE 2: Geração de Rascunho e Contagem de Páginas ---
        print("[DEBUG] ReportGenerator: Iniciando FASE 2 - Geração de Rascunho e Contagem.")
        draft_pdf_paths = []
        for data in collected_data:
            full_context = {**global_context, **data['context']}
            full_context['custom_title'] = data['instance'].get('title', 'Análise')
            full_context['new_page'] = data['instance'].get('config', {}).get('newPage', False)
            template_path = f"reports/modules/{data['key']}.html"
            temp_pdf_path = self.pdf_builder.html_to_pdf_path(template_path, full_context)
            draft_pdf_paths.append(temp_pdf_path)

        cover_page_path = self.pdf_builder.build_cover_page(global_context)
        
        # O pdf_builder junta os PDFs e retorna o número total de páginas
        total_pages = self.pdf_builder.count_merged_pages(draft_pdf_paths, cover_page_path)
        print(f"[DEBUG] ReportGenerator: Contagem finalizada. Total de páginas do relatório: {total_pages}")
        
        # Limpa os PDFs de rascunho
        self.pdf_builder._cleanup(draft_pdf_paths)

        # --- FASE 3: Geração Final com Paginação Correta ---
        print("[DEBUG] ReportGenerator: Iniciando FASE 3 - Geração Final.")
        final_pdf_paths = []
        # Adiciona o total de páginas ao contexto
        global_context['total_pages'] = total_pages
        
        for data in collected_data:
            full_context = {**global_context, **data['context']}
            full_context['custom_title'] = data['instance'].get('title', 'Análise')
            full_context['new_page'] = data['instance'].get('config', {}).get('newPage', False)
            template_path = f"reports/modules/{data['key']}.html"
            temp_pdf_path = self.pdf_builder.html_to_pdf_path(template_path, full_context)
            final_pdf_paths.append(temp_pdf_path)

        # Junta os PDFs finais com a capa
        report_name = self.config.get('report_name', 'Relatorio').replace(' ', '_')
        final_pdf_path = self.pdf_builder.merge_pdfs(
            pdf_paths=final_pdf_paths,
            output_filename=f"{report_name}_{self.client.name}_{uuid.uuid4().hex[:8]}.pdf",
            cover_page_path=cover_page_path
        )
        return final_pdf_path