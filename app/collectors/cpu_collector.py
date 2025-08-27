# ==== AURA_V2/app/collectors/cpu_collector.py (VERSÃO FINAL COM CUSTOMIZAÇÃO) ====

from .base_collector import BaseCollector
import pandas as pd

class CpuCollector(BaseCollector):
    platform = 'Zabbix'
    CPU_KEYS = ['system.cpu.util', 'hrProcessorLoad']

    @classmethod
    def is_supported(cls, platform_service, host_ids):
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
        """Busca dados e os processa de acordo com a configuração da instância."""
        
        # Pega a configuração específica desta instância
        config = instance_config.get('config', {})
        analysis_type = config.get('analysis', 'average') # Padrão é 'average'
        custom_title = instance_config.get('title', 'Análise de CPU')

        # --- A busca de dados é a mesma para todos os tipos de análise ---
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
        df.dropna(subset=['value'], inplace=True)
        if df.empty: return None

        host_map = {host['hostid']: host['name'] for host in self.service.get('host.get', {'output': ['hostid', 'name'], 'hostids': self.host_ids})}
        item_map = {item['itemid']: host_map.get(item['hostid']) for item in cpu_items}
        df['host'] = df['itemid'].map(item_map)

        # --- LÓGICA CONDICIONAL: AQUI A MÁGICA ACONTECE ---
        
        # 1. Agrega os dados brutos (calcula a média por host)
        avg_cpu_usage = df.groupby('host')['value'].mean().reset_index()
        avg_cpu_usage.rename(columns={'value': 'avg_usage'}, inplace=True)
        avg_cpu_usage['avg_usage'] = avg_cpu_usage['avg_usage'].round(2)

        # 2. Aplica a análise personalizada
        if analysis_type == 'top_n':
            n_value = config.get('value', 5)
            final_df = avg_cpu_usage.nlargest(n_value, 'avg_usage')
        # Adicione aqui a lógica para 'timeline' no futuro
        # elif analysis_type == 'timeline':
        #     final_df = ... 
        else: # 'average' (padrão)
            final_df = avg_cpu_usage

        if final_df.empty: return None

        # 3. Gera o gráfico com o título e os dados corretos
        chart_path = self.charting.generate_bar_chart(
            df=final_df, x='host', y='avg_usage',
            title=custom_title, # Usa o título personalizado
            xlabel='Host', ylabel='Uso Médio de CPU (%)'
        )

        return {
            'table_html': final_df.to_html(classes='table table-striped', index=False, border=0),
            'chart_path': chart_path
        }