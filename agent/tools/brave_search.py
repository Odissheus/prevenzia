from langchain.tools import tool
import requests
import os

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

@tool
def brave_search(query: str) -> str:
    """Cerca su internet usando Brave Search API.
    
    Args:
        query: Query di ricerca (es: 'ASL Lombardia prenotazione mammografia CUP online')
    
    Returns:
        Risultati top 5 con titoli, descrizioni e URL
    """
    
    if not BRAVE_API_KEY:
        return "Errore: BRAVE_API_KEY non configurata"
    
    try:
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": BRAVE_API_KEY
            },
            params={
                "q": query,
                "count": 5,
                "country": "IT",
                "search_lang": "it",
                "safesearch": "off"
            },
            timeout=10
        )
        
        if response.status_code != 200:
            return f"Errore ricerca Brave: HTTP {response.status_code}"
        
        data = response.json()
        results = data.get("web", {}).get("results", [])
        
        if not results:
            return "Nessun risultato trovato"
        
        output = []
        for i, result in enumerate(results, 1):
            title = result.get('title', 'N/A')
            url = result.get('url', 'N/A')
            description = result.get('description', 'N/A')
            
            output.append(f"""
[Risultato {i}]
Titolo: {title}
URL: {url}
Descrizione: {description}
---""")
        
        return "\n".join(output)
        
    except requests.Timeout:
        return "Errore: Timeout richiesta Brave Search"
    except Exception as e:
        return f"Errore Brave Search: {str(e)}"