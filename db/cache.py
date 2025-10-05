import os
import json
from typing import Optional, List, Dict

# Per ora implementazione semplice senza Redis
# Aggiungeremo Redis dopo se necessario

class SimpleCache:
    """Cache in-memory semplice (sarà sostituita con Redis)"""
    
    def __init__(self):
        self.cache = {}
    
    def get(self, key: str) -> Optional[str]:
        return self.cache.get(key)
    
    def set(self, key: str, value: str, expire: int = 3600):
        self.cache[key] = value
    
    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]

# Istanza globale
cache = SimpleCache()

def make_cache_key(regione: str, comune: str, screening_types: List[str]) -> str:
    """Crea chiave cache univoca"""
    types_str = "_".join(sorted(screening_types))
    return f"links:{regione}:{comune}:{types_str}"