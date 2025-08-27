# ==== AURA_V2/app/collectors/cpu_collector.py ====

from .base_collector import BaseCollector
import pandas as pd

class CpuCollector(BaseCollector):
    """Coletor para dados de utilização de CPU."""
    platform = 'Zabbix'
    CPU_KEYS = ['system.cpu.util', 'hrProcessorLoad']

    @classmethod
    def is_supported(cls, platform_service, host_ids):
        """Verifica se os hosts selecionados possuem itens de monitoramento de CPU."""
        if not host_ids:
            return False
        
        try:
            cpu_items = platform_service.get('item.get', {
                'output': ['itemid'], 'hostids': host_ids,
                'search': {'key_': cls.CPU_KEYS}, 'searchByAny': True, 'limit': 1
            })
            return bool(cpu_items)
        except Exception as e:
            print(f"Erro ao verificar suporte para CpuCollector: {e}")
            return False

    def fetch_data(self):
        """Busca dados do Zabbix, processa com Pandas e gera um gráfico."""
        cpu_items = self.service.get('item.get', {
            'output': ['itemid', 'hostid'], 'hostids': self.host_ids,
            'search': {'key_': self.CPU_KEYS}, 'searchByAny': True
        })
        if not cpu_items: return None

        item_ids = [item['itemid'] for item in cpu_items]
        history = self._get_history(item_ids, history_type=0) # 0 para valores numéricos (float)
        if not history: return None

        # Transformação de dados com Pandas
        df = pd.DataFrame(history)
        df['value'] = pd.to_numeric(df['value'], errors='coerce').astype(float)
        df.dropna(subset=['value'], inplace=True)
        if df.empty: return None

        # Mapeamento de IDs para nomes
        host_map = {host['hostid']: host['name'] for host in self.service.get('host.get', {'output': ['hostid', 'name'], 'hostids': self.host_ids})}
        item_map = {item['itemid']: host_map.get(item['hostid']) for item in cpu_items}
        df['host'] = df['itemid'].map(item_map)

        # Agregação dos dados: calcular a média de uso de CPU por host
        avg_cpu_usage = df.groupby('host')['value'].mean().reset_index()
        avg_cpu_usage.rename(columns={'value': 'avg_usage'}, inplace=True)
        avg_cpu_usage['avg_usage'] = avg_cpu_usage['avg_usage'].round(2)

        # Geração do gráfico
        chart_path = self.charting.generate_bar_chart(
            df=avg_cpu_usage, x='host', y='avg_usage',
            title='Média de Utilização de CPU (%) por Host',
            xlabel='Host', ylabel='Uso Médio de CPU (%)'
        )

        return {
            'table_html': avg_cpu_usage.to_html(classes='table table-striped', index=False, border=0),
            'chart_path': chart_path
        }