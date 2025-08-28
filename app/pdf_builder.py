# ==== AURA_V2/app/pdf_builder.py (VERSÃO COM CONTAGEM DE PÁGINAS) ====

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
        print(f"[DEBUG] PDFBuilder: A limpar {len(paths_to_clean)} ficheiros temporários.")
        for filename in paths_to_clean:
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
            pisa_status = pisa.CreatePDF(html, dest=result_file)
        
        if pisa_status.err:
            raise IOError(f"Erro ao converter HTML para PDF no template {template_name}: {pisa_status.err}")
        
        # print(f"[DEBUG] PDFBuilder: Template '{template_name}' convertido para PDF em '{temp_filename}'.") # Removido para reduzir o ruído no log
        return temp_filename

    def build_cover_page(self, context):
        """Renderiza e cria o PDF da página de capa."""
        print("[DEBUG] PDFBuilder: A construir a página de capa.")
        return self.html_to_pdf_path('reports/cover_page.html', context)

    # NOVO: Método que apenas junta e conta as páginas, sem guardar o ficheiro.
    def count_merged_pages(self, pdf_paths, cover_page_path=None):
        """Junta uma lista de PDFs em memória para contar o número total de páginas."""
        total_pages = 0
        
        if cover_page_path:
            try:
                cover_reader = PdfReader(cover_page_path)
                num_pages = len(cover_reader.pages)
                print(f"[DEBUG] PDFBuilder(Count): A capa tem {num_pages} página(s).")
                total_pages += num_pages
            except Exception as e:
                print(f"Erro ao contar páginas da capa {cover_page_path}: {e}")

        for path in pdf_paths:
            try:
                pdf_reader = PdfReader(path)
                num_pages = len(pdf_reader.pages)
                print(f"[DEBUG] PDFBuilder(Count): Ficheiro '{os.path.basename(path)}' tem {num_pages} página(s).")
                total_pages += num_pages
            except Exception as e:
                print(f"Erro ao contar páginas do ficheiro {path}: {e}")
        
        return total_pages

    def merge_pdfs(self, pdf_paths, output_filename='relatorio_final.pdf', cover_page_path=None):
        """Junta uma lista de ficheiros PDF num único ficheiro de saída, adicionando uma capa se fornecida."""
        pdf_writer = PdfWriter()
        temp_files_to_clean = list(pdf_paths)

        if cover_page_path:
            try:
                cover_reader = PdfReader(cover_page_path)
                for page in cover_reader.pages:
                    pdf_writer.add_page(page)
                temp_files_to_clean.append(cover_page_path)
            except Exception as e:
                print(f"Erro ao processar a capa do PDF {cover_page_path}: {e}")

        for path in pdf_paths:
            try:
                pdf_reader = PdfReader(path)
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
            except Exception as e:
                print(f"Erro ao processar o ficheiro PDF temporário {path}: {e}")

        final_pdf_path = os.path.join(self.output_dir, output_filename)
        with open(final_pdf_path, 'wb') as out:
            pdf_writer.write(out)
            
        self._cleanup(temp_files_to_clean)
        print(f"[DEBUG] PDFBuilder: Relatório final gerado com sucesso em '{final_pdf_path}'.")
        return final_pdf_path