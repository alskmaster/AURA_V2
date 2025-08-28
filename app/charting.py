# ==== AURA_V2/app/charting.py (VERSÃO COM GRÁFICOS INTELIGENTES E LEGÍVEIS) ====

import os
import uuid
import matplotlib
matplotlib.use('Agg') # Modo não-interativo, essencial para servidores web
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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
        """Salva a figura atual, ajusta o layout e fecha-a para libertar memória."""
        filename = f"{filename_prefix}_{uuid.uuid4().hex[:12]}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        # O comando plt.tight_layout() ajusta automaticamente os espaçamentos
        # para garantir que os rótulos não fiquem sobrepostos ou cortados.
        plt.tight_layout()
        
        plt.savefig(filepath, dpi=150)
        plt.close()
        
        return filepath

    def generate_bar_chart(self, df, x, y, title, xlabel, ylabel):
        """Gera um gráfico de barras legível, usando barras horizontais para melhor visualização."""
        if df.empty:
            return None
        
        num_items = len(df[x].unique())
        
        # Ajuste dinâmico da altura da figura com base no número de itens.
        # Gráficos com mais itens serão mais altos para acomodar os rótulos.
        altura_grafico = max(6, 2 + num_items * 0.4)
        print(f"[DEBUG] ChartingService: Gerando gráfico de barras com {num_items} itens. Altura calculada: {altura_grafico}")
        
        plt.figure(figsize=(10, altura_grafico))
        
        palette = sns.color_palette("viridis", min(num_items, 20))
        
        # CORREÇÃO: Alterado para gráfico de barras horizontais (barplot com orient='h').
        # Esta orientação é muito superior para lidar com rótulos longos.
        ax = sns.barplot(data=df.sort_values(by=y, ascending=True), x=y, y=x, palette=palette, hue=y, legend=False, orient='h')
        
        ax.set_title(title, fontsize=16, weight='bold')
        ax.set_xlabel(ylabel, fontsize=12) # Eixos invertidos para gráfico horizontal
        ax.set_ylabel(xlabel, fontsize=12) # Eixos invertidos para gráfico horizontal
        
        return self._save_chart(filename_prefix='bar_chart')

    def generate_time_series_chart(self, df, x, y, group_by, title, xlabel, ylabel):
        """Gera um gráfico de linha (série temporal), limitando a 10 séries para clareza."""
        if df.empty:
            return None

        plt.figure(figsize=(12, 7))
        
        # Limita o número de séries no gráfico para evitar poluição visual.
        # Seleciona as 10 séries com a maior média de valor.
        top_series = df.groupby(group_by)[y].mean().nlargest(10).index
        df_filtered = df[df[group_by].isin(top_series)]
        
        print(f"[DEBUG] ChartingService: Gerando gráfico de linha com as top {len(top_series)} séries.")

        ax = sns.lineplot(data=df_filtered, x=x, y=y, hue=group_by, marker='o', palette='tab10')
        
        ax.set_title(title, fontsize=16, weight='bold')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=30, ha='right')
        plt.legend(title=group_by.capitalize())
        
        return self._save_chart(filename_prefix='timeseries_chart')