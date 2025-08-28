# ==== AURA_V2/app/collectors/cpu_collector.py (VERSÃO COM CAMADA DE INTELIGÊNCIA) ====

from .base_collector import BaseCollector
import pandas as pd

class CpuCollector(BaseCollector):
    platform = 'Zabbix'
    CPU_KEYS = ['system.cpu.util', 'hrProcessorLoad']

    @classmethod
    def is_supported(cls, platform_service, host_ids):
        # ... (código existente, sem alterações)
        if not host_ids: return False
        try:
            cpu_items = platform_service.get('item.get', {
                'output': ['itemid'], 'hostids': host_ids,
                'search': {'key_': cls.CPU_KEYS}, 'searchByAny': True, 'limit': 1
            })
            return bool(cpu_items)
        except Exception as e:
            print(f"Erro ao verificar suporte para CpuCollector: {e}")
            return False

    def fetch_data(self, instance_config):
        """Busca dados, processa-os, gera um gráfico e extrai insights."""
        
        config = instance_config.get('config', {})
        analysis_type = config.get('analysis', 'average')
        custom_title = instance_config.get('title', 'Análise de CPU')

        # --- Etapa 1: Coleta e Preparação de Dados (Igual à anterior) ---
        cpu_items = self.service.get('item.get', {
            'output': ['itemid', 'hostid'], 'hostids': self.host_ids,
            'search': {'key_': self.CPU_KEYS}, 'searchByAny': True
        })
        if not cpu_items: return None
        item_ids = [item['itemid'] for item in cpu_items]
        history = self._get_history(item_ids, history_type=0)
        if not history: return None
        df = pd.DataFrame(history)
        df['value'] = pd.to_numeric(df['value'], errors='coerce').astype(float)
        df['clock'] = pd.to_datetime(df['clock'], unit='s')
        df.dropna(subset=['value'], inplace=True)
        if df.empty: return None
        host_map = {host['hostid']: host['name'] for host in self.service.get('host.get', {'output': ['hostid', 'name'], 'hostids': self.host_ids})}
        item_map = {item['itemid']: host_map.get(item['hostid']) for item in cpu_items}
        df['host'] = df['itemid'].map(item_map)

        # --- Etapa 2: Lógica de Análise (Igual à anterior) ---
        final_df = None
        chart_path = None
        insights = [] # Lista para guardar as nossas conclusões

        # --- NOVA ETAPA 3: GERAÇÃO DE INSIGHTS ---
        # Esta análise é feita ANTES de filtrar para o Top N, para termos uma visão completa.
        descriptive_stats = df.groupby('host')['value'].agg(['min', 'max', 'mean'])
        for host, stats in descriptive_stats.iterrows():
            if stats['max'] > 95.0:
                insights.append(f"PICO CRÍTICO: O host '{host}' atingiu um pico de utilização de CPU de {stats['max']:.2f}%, indicando um risco elevado de sobrecarga e lentidão.")
            elif stats['max'] > 85.0:
                insights.append(f"PONTO DE ATENÇÃO: O host '{host}' atingiu um pico de utilização de CPU de {stats['max']:.2f}%, sugerindo a necessidade de investigar a carga de trabalho.")
            if stats['mean'] > 75.0:
                 insights.append(f"UTILIZAÇÃO ELEVADA: O host '{host}' apresenta uma utilização média de CPU de {stats['mean']:.2f}%, o que pode indicar a necessidade de otimização ou de mais recursos a médio prazo.")

        # --- Etapa 4: Análise e Visualização Personalizada (Lógica adaptada) ---

        if analysis_type == 'timeline':
            daily_avg = df.set_index('clock').resample('D')['value'].mean().reset_index()
            daily_avg.rename(columns={'value': 'avg_daily_usage'}, inplace=True)
            daily_avg['avg_daily_usage'] = daily_avg['avg_daily_usage'].round(2)
            final_df = daily_avg
            chart_path = self.charting.generate_time_series_chart(
                df=final_df, x='clock', y='avg_daily_usage',
                title=custom_title, xlabel='Data', ylabel='Uso Médio de CPU (%)'
            )
        
        elif analysis_type == 'top_n':
            n_value = config.get('value', 5)
            # A agregação avançada agora vem da nossa análise de insights
            final_df = descriptive_stats.reset_index().rename(columns={'mean': 'avg_usage', 'min': 'min_usage', 'max': 'max_usage'})
            final_df = final_df.nlargest(n_value, 'avg_usage')
            for col in ['min_usage', 'max_usage', 'avg_usage']:
                final_df[col] = final_df[col].round(2)
            
            chart_path = self.charting.generate_bar_chart(
                df=final_df, x='host', y='avg_usage',
                title=custom_title, xlabel='Host', ylabel='Uso Médio de CPU (%)'
            )

        else: # 'average'
            final_df = descriptive_stats.reset_index()[['host', 'mean']].rename(columns={'mean': 'avg_usage'})
            final_df['avg_usage'] = final_df['avg_usage'].round(2)
            chart_path = self.charting.generate_bar_chart(
                df=final_df, x='host', y='avg_usage',
                title=custom_title, xlabel='Host', ylabel='Uso Médio de CPU (%)'
            )

        return {
            'table_html': final_df.to_html(classes='table table-striped', index=False, border=0),
            'chart_path': chart_path,
            'insights': insights # Retorna a lista de conclusões
        }