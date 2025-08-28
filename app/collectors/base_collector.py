# ==== AURA_V2/app/collectors/base_collector.py (VERSÃO CORRIGIDA E COMPLETA) ====

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

    # CORREÇÃO: O método 'collect' agora é o método principal e abstrato.
    # A lógica de try/except foi movida para o ReportGenerator, que é um local mais
    # apropriado para tratar erros de execução de um coletor.
    @abstractmethod
    def collect(self, instance_config=None):
        """
        Método abstrato que cada coletor filho DEVE implementar.
        Ele recebe a configuração específica da sua instância no relatório.
        """
        pass

    @classmethod
    @abstractmethod
    def is_supported(cls, platform_service, host_ids):
        """
        Método abstrato para verificar se o coletor é compatível
        com os hosts selecionados.
        """
        pass

    # --- FUNÇÕES DE AJUDA ---
    # Estas funções continuam a ser úteis para todos os coletores filhos.
    def _get_items_by_key(self, key_pattern, host_ids=None):
        """Função de ajuda para buscar itens com base num padrão de chave."""
        active_host_ids = host_ids if host_ids is not None else self.host_ids
        if not active_host_ids:
            return []
        
        # DEBUG: Adicionado para ver que itens estão a ser pesquisados
        print(f"[DEBUG] BaseCollector._get_items_by_key: Buscando itens com o padrão '{key_pattern}' para {len(active_host_ids)} hosts.")
        
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
        
        # DEBUG: Adicionado para ver que histórico está a ser solicitado
        print(f"[DEBUG] BaseCollector._get_history: Buscando histórico para {len(item_ids)} itens do tipo {history_type}.")
        
        return self.service.get('history.get', {
            'output': 'extend',
            'history': history_type,
            'itemids': item_ids,
            'time_from': self.start_time,
            'time_till': self.end_time,
            'sortfield': 'clock',
            'sortorder': 'ASC'
        })