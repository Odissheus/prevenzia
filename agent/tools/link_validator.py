from langchain.tools import tool
import requests

@tool
def validate_link(url: str) -> str:
    """Verifica che un URL sia attivo e raggiungibile.
    
    Args:
        url: URL completo da verificare (es: https://...)
    
    Returns:
        Status del link e codice HTTP
    """
    
    try:
        response = requests.head(
            url,
            timeout=5,
            allow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        status_code = response.status_code
        
        if status_code < 400:
            return f"✓ Link attivo (HTTP {status_code})"
        elif status_code == 404:
            return f"✗ Pagina non trovata (HTTP 404)"
        elif status_code >= 500:
            return f"⚠ Errore server (HTTP {status_code})"
        else:
            return f"⚠ Problema accesso (HTTP {status_code})"
            
    except requests.Timeout:
        return "✗ Timeout - link troppo lento o irraggiungibile"
    except requests.ConnectionError:
        return "✗ Impossibile connettersi - link probabilmente non valido"
    except Exception as e:
        return f"✗ Errore validazione: {str(e)}"