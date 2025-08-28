# ==== AURA_V2/app/report_generator.py (VERSÃO MODIFICADA E COMPLETA) ====

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
        """Executa o processo de geração do relatório, incluindo a capa e os módulos configurados."""
        pdf_parts_paths = []
        has_data = False

        # --- NOVO: Preparar contexto global para o relatório ---
        start_date_str = self.config.get('start_date')
        end_date_str = self.config.get('end_date')
        
        global_context = {
            'report_name': self.config.get('report_name', 'Relatório de Análise'),
            'client_name': self.client.name,
            'start_date': datetime.strptime(start_date_str, '%Y-%m-%d').strftime('%d/%m/%Y') if start_date_str else 'N/D',
            'end_date': datetime.strptime(end_date_str, '%Y-%m-%d').strftime('%d/%m/%Y') if end_date_str else 'N/D'
        }
        print(f"[DEBUG] ReportGenerator: Contexto global criado: {global_context}")

        # --- NOVO: Gerar a página de capa ---
        cover_page_path = self.pdf_builder.build_cover_page(global_context)
        if not cover_page_path:
            current_app.logger.error("Falha ao gerar a página de capa do relatório.")
            return None

        # Itera sobre a lista de instâncias de módulos configuradas pelo utilizador no layout
        for module_instance in self.config.get('modules', []):
            module_key = module_instance.get('type')
            
            if module_key in AVAILABLE_COLLECTORS:
                CollectorClass = AVAILABLE_COLLECTORS[module_key]['class']
                required_platform = CollectorClass.platform
                platform_service = self.platform_services.get(required_platform)

                if platform_service:
                    collector = CollectorClass(platform_service, self.charting, self.config)
                    module_context = collector.collect(instance_config=module_instance)
                    
                    if module_context:
                        has_data = True
                        
                        # Combina o contexto global com o contexto específico do módulo
                        full_context = {**global_context, **module_context}
                        
                        # Adiciona o título e a opção de nova página ao contexto
                        full_context['custom_title'] = module_instance.get('title', 'Análise')
                        full_context['new_page'] = module_instance.get('config', {}).get('newPage', False)

                        template_path = f'reports/modules/{module_key}.html'
                        temp_pdf_path = self.pdf_builder.html_to_pdf_path(template_path, full_context)
                        pdf_parts_paths.append(temp_pdf_path)
        
        if not has_data:
            self.pdf_builder._cleanup(pdf_parts_paths + [cover_page_path])
            return None

        report_name = self.config.get('report_name', 'Relatorio').replace(' ', '_')
        final_pdf_path = self.pdf_builder.merge_pdfs(
            pdf_paths=pdf_parts_paths,
            output_filename=f"{report_name}_{self.client.name}_{uuid.uuid4().hex[:8]}.pdf",
            cover_page_path=cover_page_path # Passa o caminho da capa para a junção
        )
        return final_pdf_path