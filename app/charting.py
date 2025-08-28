# ==== AURA_V2/app/charting.py (VERSÃO MODIFICADA E COMPLETA) ====

import os
import uuid
import matplotlib
matplotlib.use('Agg') # Modo não-interativo, essencial para servidores web
import matplotlib.pyplot as plt
import matplotlib.dates as mdates # Nova importação para formatação de datas
import seaborn as sns
from flask import current_app

class ChartingService:
    """Serviço dedicado à criação de gráficos."""
    def __init__(self):
        self.output_dir = os.path.join(current_app.static_folder, 'charts')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        sns.set_theme(style="whitegrid")

    def _save_chart(self, filename_prefix='chart'):
        """Salva a figura atual e fecha-a para libertar memória."""
        filename = f"{filename_prefix}_{uuid.uuid4().hex[:12]}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        plt.savefig(filepath, bbox_inches='tight', dpi=150)
        plt.close()
        
        # Retorna o caminho absoluto do ficheiro para o gerador de PDF
        return filepath

    def generate_bar_chart(self, df, x, y, title, xlabel, ylabel):
        """Gera um gráfico de barras a partir de um DataFrame do Pandas."""
        if df.empty:
            return None
            
        plt.figure(figsize=(10, 6))
        
        # Usar um número limitado de cores se houver muitos itens para evitar sobrecarga
        num_items = len(df[x].unique())
        palette = sns.color_palette("viridis", min(num_items, 20))
        
        ax = sns.barplot(data=df, x=x, y=y, palette=palette, hue=x, legend=False)
        
        ax.set_title(title, fontsize=16, weight='bold')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        
        # Rotacionar os labels apenas se houver muitos itens
        if num_items > 5:
            plt.xticks(rotation=45, ha='right')
        
        return self._save_chart(filename_prefix='bar_chart')

    def generate_time_series_chart(self, df, x, y, group_by, title, xlabel, ylabel):
        """
        NOVO: Gera um gráfico de linha (série temporal) a partir de um DataFrame.
        Pode plotar múltiplas linhas, uma para cada item na coluna 'group_by'.
        """
        if df.empty:
            return None

        plt.figure(figsize=(12, 7))
        
        ax = sns.lineplot(data=df, x=x, y=y, hue=group_by, marker='o', palette='tab10')
        
        ax.set_title(title, fontsize=16, weight='bold')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        
        # Formatação aprimorada do eixo de data
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=30, ha='right')
        plt.legend(title=group_by.capitalize())
        
        return self._save_chart(filename_prefix='timeseries_chart')