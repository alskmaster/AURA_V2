# ==== AURA_V2/app/charting.py (VERSÃO ATUALIZADA) ====

import os
import uuid
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
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
        return filepath

    def generate_bar_chart(self, df, x, y, title, xlabel, ylabel):
        """Gera um gráfico de barras a partir de um DataFrame do Pandas."""
        if df.empty: return None
        plt.figure(figsize=(10, 6))
        palette = sns.color_palette("viridis", len(df))
        ax = sns.barplot(data=df, x=x, y=y, palette=palette, hue=x, legend=False)
        ax.set_title(title, fontsize=16, weight='bold')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        plt.xticks(rotation=45, ha='right')
        return self._save_chart(filename_prefix='bar_chart')

    # --- NOVO MÉTODO PARA LINHA DO TEMPO ---
    def generate_time_series_chart(self, df, x, y, title, xlabel, ylabel):
        """Gera um gráfico de linha do tempo."""
        if df.empty: return None
        plt.figure(figsize=(12, 6))
        ax = sns.lineplot(data=df, x=x, y=y, color='#4f46e5', marker='o')
        ax.set_title(title, fontsize=16, weight='bold')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        plt.xticks(rotation=45, ha='right')
        return self._save_chart(filename_prefix='time_series')