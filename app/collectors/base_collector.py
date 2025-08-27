# ==== AURA_V2/app/collectors/base_collector.py (VERSÃO FINAL E COMPLETA) ====

from abc import ABC, abstractmethod
import time

class BaseCollector(ABC):
    """Classe base abstrata para todos os coletores de dados."""
    platform = None

    def __init__(self, platform_service, charting_service, report_config):
        self.service = platform_service
        self.charting = charting_service
        self.config = report_config
        self.host_ids = self.config.get('hosts', [])
        
        start_date_str = self.config.get('start_date')
        end_date_str = self.config.get('end_date')

        if start_date_str and end_date_str:
            self.start_time = int(time.mktime(time.strptime(start_date_str, '%Y-%m-%d')))
            self.end_time = int(time.mktime(time.strptime(end_date_str, '%Y-%m-%d')))
        else:
            self.start_time = None
            self.end_time = None

    def collect(self, instance_config=None):
        try:
            # Passa a configuração da instância para o fetch_data
            data = self.fetch_data(instance_config)
            if data is None: return None
            return data
        except Exception as e:
            print(f"Erro ao coletar dados para {self.__class__.__name__}: {e}")
            return None

    @classmethod
    @abstractmethod
    def is_supported(cls, platform_service, host_ids):
        pass

    @abstractmethod
    def fetch_data(self, instance_config):
        pass

    # --- FUNÇÕES DE AJUDA RESTAURADAS ---
    def _get_items_by_key(self, key_pattern, host_ids=None):
        """Função de ajuda para buscar itens com base num padrão de chave."""
        active_host_ids = host_ids if host_ids is not None else self.host_ids
        if not active_host_ids:
            return []
        return self.service.get('item.get', {
            'output': ['itemid', 'name', 'hostid'],
            'hostids': active_host_ids,
            'search': {'key_': key_pattern},
            'searchByAny': True
        })

    def _get_history(self, item_ids, history_type):
        """Função de ajuda para buscar o histórico de itens."""
        if not self.start_time or not self.end_time:
            raise ValueError("Período (data de início/fim) não foi definido para buscar o histórico.")
        return self.service.get('history.get', {
            'output': 'extend',
            'history': history_type,
            'itemids': item_ids,
            'time_from': self.start_time,
            'time_till': self.end_time,
            'sortfield': 'clock',
            'sortorder': 'ASC'
        })