from langchain.tools import tool
import requests
from bs4 import BeautifulSoup

@tool
def scrape_page(url: str) -> str:
    """Scarica e analizza una pagina web per estrarre informazioni utili.
    
    Args:
        url: URL completo della pagina da analizzare
    
    Returns:
        Testo estratto della pagina e link di prenotazione trovati
    """
    
    try:
        # Download pagina
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Rimuovi elementi non utili
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
        
        # Estrai testo principale
        text = soup.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())  # Normalizza spazi
        text = text[:2000]  # Limita a 2000 caratteri
        
        # Cerca link di prenotazione
        prenota_keywords = ['prenota', 'prenotazione', 'cup', 'booking', 'appuntamento', 'accesso']
        prenota_links = []
        
        for link in soup.find_all('a', href=True):
            link_text = link.get_text().lower()
            link_href = link['href']
            
            if any(keyword in link_text for keyword in prenota_keywords):
                # Gestisci link relativi
                if link_href.startswith('/'):
                    from urllib.parse import urljoin
                    link_href = urljoin(url, link_href)
                
                prenota_links.append(f"{link_text.strip()}: {link_href}")
        
        result = f"CONTENUTO PAGINA:\n{text}\n\n"
        
        if prenota_links:
            result += f"LINK PRENOTAZIONE TROVATI:\n"
            result += "\n".join(prenota_links[:5])
        else:
            result += "Nessun link di prenotazione evidente trovato."
        
        return result
        
    except requests.Timeout:
        return f"Errore: Timeout caricamento {url}"
    except requests.HTTPError as e:
        return f"Errore HTTP: {e.response.status_code} per {url}"
    except Exception as e:
        return f"Errore analisi pagina: {str(e)}"