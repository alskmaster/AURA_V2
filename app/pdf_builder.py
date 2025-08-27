# ==== AURA_V2/app/pdf_builder.py (VERSÃO CORRIGIDA) ====

import os
import uuid
from flask import render_template
from xhtml2pdf import pisa
from PyPDF2 import PdfWriter, PdfReader

class PDFBuilderService:
    """Serviço para construir relatórios em PDF a partir de templates HTML."""
    def __init__(self, output_dir='relatorios_gerados'):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
    def _cleanup(self, paths_to_clean):
        """Remove os ficheiros PDF temporários."""
        for filename in paths_to_clean:
            # Adiciona uma verificação de segurança para apagar apenas na pasta de output
            if os.path.dirname(filename) == os.path.abspath(self.output_dir):
                try:
                    os.remove(filename)
                except OSError as e:
                    print(f"Erro ao remover ficheiro temporário {filename}: {e}")

    def html_to_pdf_path(self, template_name, context):
        """Renderiza um template HTML e converte-o para um ficheiro PDF temporário."""
        html = render_template(template_name, **context)
        temp_filename = os.path.join(self.output_dir, f"temp_{uuid.uuid4().hex}.pdf")
        
        with open(temp_filename, "w+b") as result_file:
            # --- CORREÇÃO APLICADA AQUI ---
            # A variável correta é 'html', não 'source_html'.
            pisa_status = pisa.CreatePDF(html, dest=result_file)
        
        if pisa_status.err:
            raise IOError(f"Erro ao converter HTML para PDF: {pisa_status.err}")
        
        return temp_filename
        
    def merge_pdfs(self, pdf_paths, output_filename='relatorio_final.pdf'):
        """Junta uma lista de ficheiros PDF num único ficheiro de saída."""
        pdf_writer = PdfWriter()
        temp_files_to_clean = []

        for path in pdf_paths:
            try:
                pdf_reader = PdfReader(path)
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
                temp_files_to_clean.append(path)
            except Exception as e:
                print(f"Erro ao processar o ficheiro PDF temporário {path}: {e}")

        final_pdf_path = os.path.join(self.output_dir, output_filename)
        with open(final_pdf_path, 'wb') as out:
            pdf_writer.write(out)
            
        self._cleanup(temp_files_to_clean) # Limpa os ficheiros temporários após a junção
        return final_pdf_path