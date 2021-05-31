from data_model import Service
from typing import Dict
# RegistedService is a simple map for caching service metadata
# there should be little data,so keep it in memory
RegistedService: Dict[str, Service] = {}

# add SQLite afterwards
