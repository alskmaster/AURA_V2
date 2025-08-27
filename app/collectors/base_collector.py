# ==== AURA_V2/app/collectors/base_collector.py ====

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

    def collect(self):
        try:
            data = self.fetch_data()
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
    def fetch_data(self):
        pass