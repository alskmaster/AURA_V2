# ==== AURA_V2/app/collectors/base_collector.py (VERSÃO ROBUSTA COM CHUNKING) ====

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
    def _get_items_by_key(self, key_pattern, host_ids=None):
        """Função de ajuda para buscar itens com base num padrão de chave."""
        active_host_ids = host_ids if host_ids is not None else self.host_ids
        if not active_host_ids:
            return []
        
        print(f"[DEBUG] BaseCollector._get_items_by_key: Buscando itens com o padrão '{key_pattern}' para {len(active_host_ids)} hosts.")
        
        return self.service.get('item.get', {
            'output': ['itemid', 'name', 'hostid'],
            'hostids': active_host_ids,
            'search': {'key_': key_pattern},
            'searchByAny': True
        })

    def _get_history(self, item_ids, history_type, chunk_size=5):
        """
        Função de ajuda para buscar o histórico de itens, agora com 'chunking'
        para evitar sobrecarregar a API do Zabbix.
        """
        if not self.start_time or not self.end_time:
            raise ValueError("Período (data de início/fim) não foi definido para buscar o histórico.")
        
        if not item_ids:
            return []

        all_history = []
        # Divide a lista de item_ids em lotes (chunks)
        item_chunks = [item_ids[i:i + chunk_size] for i in range(0, len(item_ids), chunk_size)]
        
        print(f"[DEBUG] BaseCollector._get_history: A lista de {len(item_ids)} itens foi dividida em {len(item_chunks)} lotes de até {chunk_size} itens cada.")

        for i, chunk in enumerate(item_chunks):
            print(f"[DEBUG] BaseCollector._get_history: Buscando histórico para o lote {i + 1}/{len(item_chunks)}...")
            try:
                history_chunk = self.service.get('history.get', {
                    'output': 'extend',
                    'history': history_type,
                    'itemids': chunk,
                    'time_from': self.start_time,
                    'time_till': self.end_time,
                    'sortfield': 'clock',
                    'sortorder': 'ASC'
                })
                if history_chunk:
                    all_history.extend(history_chunk)
                    print(f"[DEBUG] BaseCollector._get_history: Lote {i + 1} retornou {len(history_chunk)} registos.")
                else:
                    print(f"[DEBUG] BaseCollector._get_history: Lote {i + 1} não retornou dados.")
                # Pausa opcional para ser ainda mais "gentil" com a API
                time.sleep(0.1) 
            except Exception as e:
                print(f"[ERRO] BaseCollector._get_history: Falha ao buscar o lote {i + 1}. Erro: {e}")
                # Decide se quer parar ou continuar em caso de erro. Continuar é mais resiliente.
                continue
        
        print(f"[DEBUG] BaseCollector._get_history: Coleta de histórico finalizada. Total de {len(all_history)} registos obtidos.")
        return all_history