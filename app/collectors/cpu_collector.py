# ==== AURA_V2/app/collectors/cpu_collector.py (VERSÃO COM COMPONENTES CONDICIONAIS) ====

from .base_collector import BaseCollector
import pandas as pd

class CpuCollector(BaseCollector):
    """Coletor customizável para dados de utilização de CPU com camada de inteligência."""
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

    def collect(self, instance_config):
        """
        Busca dados, processa-os e gera apenas os componentes (insights, gráfico, tabela)
        solicitados na configuração da instância.
        """
        
        config = instance_config.get('config', {})
        analysis_type = config.get('analysis', 'average')
        
        # NOVO: Ler as opções de visibilidade, com True como padrão
        show_insights = config.get('showInsights', True)
        show_chart = config.get('showChart', True)
        show_table = config.get('showTable', True)

        print(f"[DEBUG] CpuCollector: Configurações recebidas -> analysis: {analysis_type}, showInsights: {show_insights}, showChart: {show_chart}, showTable: {show_table}")

        # --- Etapa 1: Coleta e Preparação de Dados (Sempre necessária) ---
        cpu_items = self._get_items_by_key(self.CPU_KEYS)
        if not cpu_items: return None

        item_ids = [item['itemid'] for item in cpu_items]
        history = self._get_history(item_ids, history_type=0)
        if not history: return None
        
        df = pd.DataFrame(history)
        print(f"[DEBUG] CpuCollector: DataFrame inicial criado com {len(df)} registos de histórico.")

        df['value'] = pd.to_numeric(df['value'], errors='coerce').astype(float)
        df['clock'] = pd.to_datetime(df['clock'], unit='s')
        df.dropna(subset=['value'], inplace=True)
        if df.empty: return None
        
        host_map = {host['hostid']: host['name'] for host in self.service.get('host.get', {'output': ['hostid', 'name'], 'hostids': self.host_ids})}
        item_map = {item['itemid']: host_map.get(item['hostid']) for item in cpu_items}
        df['host'] = df['itemid'].map(item_map)

        # --- Etapa 2: Geração de Insights (Condicional) ---
        insights = []
        if show_insights:
            print("[DEBUG] CpuCollector: Gerando Insights...")
            descriptive_stats_insights = df.groupby('host')['value'].agg(['min', 'max', 'mean'])
            for host, stats in descriptive_stats_insights.iterrows():
                if stats['max'] > 95.0:
                    insights.append(f"PICO CRÍTICO: O host '{host}' atingiu um pico de utilização de CPU de {stats['max']:.2f}%, indicando um risco elevado de sobrecarga e lentidão.")
                elif stats['max'] > 85.0:
                    insights.append(f"PONTO DE ATENÇÃO: O host '{host}' atingiu um pico de utilização de CPU de {stats['max']:.2f}%, sugerindo a necessidade de investigar a carga de trabalho.")
                if stats['mean'] > 75.0:
                     insights.append(f"UTILIZAÇÃO ELEVADA: O host '{host}' apresenta uma utilização média de CPU de {stats['mean']:.2f}%, o que pode indicar a necessidade de otimização ou de mais recursos a médio prazo.")
            if not insights:
                insights.append("ANÁLISE NORMAL: Nenhum host apresentou picos de uso de CPU acima de 85% ou média acima de 75% durante o período analisado.")

        # --- Etapa 3: Análise e Visualização (O processamento depende do que será exibido) ---
        final_df = None
        chart_path = None
        table_html = None
        
        # O processamento de dados só é necessário se o gráfico ou a tabela forem exibidos
        if show_chart or show_table:
            print("[DEBUG] CpuCollector: Processando dados para gráfico e/ou tabela...")
            descriptive_stats = df.groupby('host')['value'].agg(['min', 'max', 'mean'])

            if analysis_type == 'timeline':
                daily_avg = df.set_index('clock').groupby('host')['value'].resample('D').mean().reset_index()
                daily_avg.rename(columns={'value': 'avg_daily_usage'}, inplace=True)
                daily_avg['avg_daily_usage'] = daily_avg['avg_daily_usage'].round(2)
                final_df = daily_avg
            
            elif analysis_type == 'top_n':
                n_value = int(config.get('value', 5))
                final_df = descriptive_stats.reset_index().rename(columns={'mean': 'avg_usage', 'min': 'min_usage', 'max': 'max_usage'})
                final_df = final_df.nlargest(n_value, 'avg_usage')
                for col in ['min_usage', 'max_usage', 'avg_usage']:
                    final_df[col] = final_df[col].round(2)
            
            else: # Padrão 'average'
                final_df = descriptive_stats.reset_index()[['host', 'mean']].rename(columns={'mean': 'avg_usage'})
                final_df = final_df.sort_values(by='avg_usage', ascending=False)
                final_df['avg_usage'] = final_df['avg_usage'].round(2)

            # Geração do Gráfico (Condicional)
            if show_chart and final_df is not None:
                print("[DEBUG] CpuCollector: Gerando Gráfico...")
                chart_args = {
                    'df': final_df, 'title': instance_config.get('title', 'Análise de Utilização de CPU'), 
                    'xlabel': 'Host', 'ylabel': 'Uso Médio de CPU (%)'
                }
                if analysis_type == 'timeline':
                    chart_path = self.charting.generate_time_series_chart(
                        x='clock', y='avg_daily_usage', group_by='host', **chart_args
                    )
                else:
                    chart_path = self.charting.generate_bar_chart(
                        x='host', y='avg_usage', **chart_args
                    )
            
            # Geração da Tabela (Condicional)
            if show_table and final_df is not None:
                print("[DEBUG] CpuCollector: Gerando Tabela HTML...")
                table_html = final_df.to_html(classes='table table-striped', index=False, border=0)

        # --- Etapa 4: Retorno do Contexto para o Template ---
        return {
            'table_html': table_html,
            'chart_path': chart_path,
            'insights': insights
        }