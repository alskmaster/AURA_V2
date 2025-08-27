# ==== AURA_V2/app/report_generator.py (VERSÃO FINAL COM CUSTOMIZAÇÃO) ====

import uuid
import os
from flask import current_app
from .zabbix_api import ZabbixService
from .charting import ChartingService
from .pdf_builder import PDFBuilderService
from .models import DataSource
from .collectors import AVAILABLE_COLLECTORS

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
                try: self.platform_services[platform_name] = ZabbixService(ds)
                except Exception as e: print(f"Falha ao inicializar serviço Zabbix: {e}")

    def generate(self):
        """Executa o processo de geração do relatório."""
        pdf_parts_paths = []
        has_data = False

        # Itera sobre a lista de instâncias de módulos configuradas pelo utilizador
        for module_instance in self.config.get('modules', []):
            module_key = module_instance.get('type')
            
            if module_key in AVAILABLE_COLLECTORS:
                CollectorClass = AVAILABLE_COLLECTORS[module_key]['class']
                required_platform = CollectorClass.platform
                platform_service = self.platform_services.get(required_platform)

                if platform_service:
                    # Passa a configuração específica da instância para o coletor
                    collector = CollectorClass(platform_service, self.charting, self.config)
                    module_context = collector.collect(instance_config=module_instance)
                    
                    if module_context:
                        has_data = True
                        # Adiciona o título personalizado ao contexto para o template do PDF
                        module_context['custom_title'] = module_instance.get('title', 'Análise')
                        
                        template_path = f'reports/modules/{module_key}.html'
                        temp_pdf_path = self.pdf_builder.html_to_pdf_path(template_path, module_context)
                        pdf_parts_paths.append(temp_pdf_path)
        
        if not has_data:
            self.pdf_builder._cleanup(pdf_parts_paths)
            return None

        report_name = self.config.get('report_name', 'Relatorio').replace(' ', '_')
        final_pdf_path = self.pdf_builder.merge_pdfs(
            pdf_paths=pdf_parts_paths,
            output_filename=f"{report_name}_{self.client.name}_{uuid.uuid4().hex[:8]}.pdf"
        )
        return final_pdf_path