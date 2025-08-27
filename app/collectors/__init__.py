# ==== AURA_V2/app/collectors/__init__.py ====

# Importa as classes dos coletores
from .cpu_collector import CpuCollector
# No futuro, importe outros coletores aqui.

# Define a lista de módulos disponíveis num local central.
AVAILABLE_COLLECTORS = {
    'cpu': {'class': CpuCollector, 'name': 'Uso de CPU'},
}