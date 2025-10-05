import os
import pymysql
from typing import List, Dict, Optional

# Configurazione DB da .env
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

async def get_local_screening(eta: int, sesso: str, regione: str) -> List[Dict]:
    """Query database per screening disponibili"""
    
    connection = pymysql.connect(**DB_CONFIG)
    
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT * FROM screening_regionali 
                WHERE regione = %s 
                AND (sesso = %s OR sesso = 'TUTTI')
                AND eta_min <= %s 
                AND eta_max >= %s
                ORDER BY tipo_screening
            """
            cursor.execute(query, (regione, sesso, eta, eta))
            results = cursor.fetchall()
            return results
    
    finally:
        connection.close()

async def check_cache(regione: str, comune: str, screening_list: List[Dict]) -> Optional[List[Dict]]:
    """Controlla se ci sono link già trovati in cache"""
    
    # TODO: implementeremo Redis dopo
    # Per ora ritorna sempre None (nessuna cache)
    return None

async def save_to_cache(regione: str, comune: str, links: List[Dict]):
    """Salva link trovati in cache"""
    
    # TODO: implementeremo Redis dopo
    pass