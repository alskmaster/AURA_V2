# ==== AURA_V2/app/report_generator.py (VERSÃO DE DEBUG) ====

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

        print("\\n--- INICIANDO DEBUG: ReportGenerator __init__ ---")
        print(f"[DEBUG] Configurações recebidas: {self.config}")

        for ds in self.client.data_sources:
            platform_name = ds.platform.capitalize()
            print(f"[DEBUG] A processar DataSource da plataforma: {platform_name}")
            if platform_name == 'Zabbix':
                try:
                    self.platform_services[platform_name] = ZabbixService(ds)
                    print(f"[DEBUG] ZabbixService para o cliente '{self.client.name}' inicializado com SUCESSO.")
                except Exception as e:
                    print(f"[DEBUG] ERRO ao inicializar ZabbixService: {e}")
        print("--- FIM DEBUG: ReportGenerator __init__ ---\\n")

    def generate(self):
        """Executa o processo de geração do relatório."""
        print("\\n--- INICIANDO DEBUG: ReportGenerator generate ---")
        pdf_parts_paths = []
        has_data = False

        module_keys = self.config.get('modules', [])
        print(f"[DEBUG] Módulos selecionados para o relatório: {module_keys}")

        for module_key in module_keys:
            if module_key in AVAILABLE_COLLECTORS:
                CollectorClass = AVAILABLE_COLLECTORS[module_key]['class']
                required_platform = CollectorClass.platform
                platform_service = self.platform_services.get(required_platform)

                print(f"\\n[DEBUG] A processar módulo: '{module_key}' (requer plataforma: '{required_platform}')")

                if platform_service:
                    print(f"[DEBUG] Serviço para '{required_platform}' encontrado. A chamar o coletor...")
                    collector = CollectorClass(platform_service, self.charting, self.config)
                    module_context = collector.collect()
                    
                    if module_context:
                        has_data = True
                        print(f"[DEBUG] SUCESSO: Coletor '{module_key}' retornou dados.")
                        module_context.update({
                            'client_name': self.client.name,
                            'report_name': self.config.get('report_name')
                        })
                        
                        template_path = f'reports/modules/{module_key}.html'
                        temp_pdf_path = self.pdf_builder.html_to_pdf_path(template_path, module_context)
                        pdf_parts_paths.append(temp_pdf_path)
                        print(f"[DEBUG] PDF temporário para '{module_key}' gerado em: {temp_pdf_path}")
                    else:
                        print(f"[DEBUG] AVISO: Coletor '{module_key}' executou, mas não retornou dados.")
                else:
                    print(f"[DEBUG] ERRO: Serviço para a plataforma '{required_platform}' não foi encontrado ou falhou na inicialização.")
        
        if not has_data:
            print("[DEBUG] Nenhum dado foi coletado por nenhum módulo. A retornar None.")
            self.pdf_builder._cleanup(pdf_parts_paths)
            print("--- FIM DEBUG: generate (sem dados) ---\\n")
            return None

        report_name = self.config.get('report_name', 'Relatorio').replace(' ', '_')
        final_pdf_path = self.pdf_builder.merge_pdfs(
            pdf_paths=pdf_parts_paths,
            output_filename=f"{report_name}_{self.client.name}_{uuid.uuid4().hex[:8]}.pdf"
        )
        print(f"[DEBUG] Relatório final gerado com sucesso em: {final_pdf_path}")
        print("--- FIM DEBUG: generate (sucesso) ---\\n")
        return final_pdf_path