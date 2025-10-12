from langchain_anthropic import ChatAnthropic
import os
import json
import re

def get_available_screenings(eta: int, sesso: str) -> list:
    """Determina quali screening sono disponibili in base a età e sesso"""
    screenings = []
    
    if sesso == 'F' and 50 <= eta <= 69:
        screenings.append({
            'tipo_screening': 'Mammografia',
            'descrizione': 'Screening tumore della mammella'
        })
    
    if sesso == 'F' and 25 <= eta <= 64:
        screenings.append({
            'tipo_screening': 'Pap-test',
            'descrizione': 'Screening tumore del collo dell\'utero'
        })
    
    if 50 <= eta <= 74:
        screenings.append({
            'tipo_screening': 'Test sangue occulto fecale',
            'descrizione': 'Screening tumore del colon-retto'
        })
    
    return screenings


async def run_screening_agent(eta: int, sesso: str, regione: str, comune: str) -> list:
    """
    Esegue l'agente AI per trovare link di prenotazione screening.
    
    Args:
        eta: Età del paziente
        sesso: Sesso del paziente ('M' o 'F')
        regione: Regione di residenza
        comune: Comune di residenza
        
    Returns:
        Lista di dizionari con i link trovati
    """
    
    print(f"📥 Ricevuta richiesta: {eta} anni, {sesso}, {comune}, {regione}")
    
    # Determina screening disponibili
    screening_list = get_available_screenings(eta, sesso)
    
    if not screening_list:
        print("⚠️ Nessuno screening disponibile per questi parametri")
        return []
    
    screening_names = [s['tipo_screening'] for s in screening_list]
    print(f"📋 Screening da cercare: {screening_names}")
    
    # Inizializza Claude
    try:
        llm = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            temperature=0.2,
            max_tokens=4096,
            anthropic_api_key=os.getenv("CLAUDE_API_KEY")
        )
        print("✅ Claude inizializzato correttamente")
    except Exception as e:
        print(f"❌ Errore inizializzazione Claude: {str(e)}")
        return []
    
    # Crea il prompt
    screening_text = ", ".join(screening_names)
    
    prompt = f"""Sei un assistente che aiuta a trovare link ufficiali per prenotare screening oncologici del Sistema Sanitario Nazionale italiano.

INFORMAZIONI PAZIENTE:
- Età: {eta} anni
- Sesso: {'Donna' if sesso == 'F' else 'Uomo'}
- Regione: {regione}
- Comune: {comune}

SCREENING DA CERCARE: {screening_text}

COMPITO:
Trova i link UFFICIALI dei portali dove è possibile prenotare questi screening nella regione {regione}.

Cerca in particolare:
1. Portale screening oncologici Regione {regione}
2. Sito ASL di {comune} o zona
3. CUP online (Centro Unico Prenotazioni) {regione}
4. Portali specifici per screening oncologici

FORMATO RISPOSTA - Restituisci SOLO un oggetto JSON in questo formato esatto:
{{
  "links": [
    {{
      "tipo_screening": "Nome screening",
      "url": "https://...",
      "nome_ente": "Nome ente (es. Regione Lombardia)",
      "note": "Breve descrizione"
    }}
  ]
}}

REGOLE IMPORTANTI:
- Includi SOLO link a siti ufficiali (.gov.it, sanita.regione.it, asl, ecc)
- URL devono essere completi e corretti
- Massimo 3 link
- Se non trovi nessun link valido, restituisci: {{"links": []}}
- NON aggiungere testo prima o dopo il JSON
- NON usare caratteri speciali non escaped negli URL"""

    print("🔍 Invio richiesta a Claude...")
    
    # Chiamata a Claude
    try:
        response = await llm.ainvoke(prompt)
        
        # Estrai il contenuto
        if hasattr(response, 'content'):
            output_text = response.content
        else:
            output_text = str(response)
        
        print("✅ Risposta ricevuta da Claude")
        print(f"Lunghezza risposta: {len(output_text)} caratteri")
        print(f"Prime 300 caratteri: {output_text[:300]}")
        
        # Estrai i link
        links = extract_links_from_response(output_text)
        
        if links:
            print(f"✅ Trovati {len(links)} link validi")
            for i, link in enumerate(links, 1):
                print(f"  {i}. {link.get('tipo_screening', 'N/A')} - {link.get('url', 'N/A')}")
        else:
            print("⚠️ Nessun link estratto dalla risposta")
        
        return links
        
    except Exception as e:
        print(f"❌ Errore durante chiamata a Claude: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def extract_links_from_response(text: str) -> list:
    """
    Estrae i link dalla risposta di Claude in modo robusto.
    Gestisce vari formati di risposta e JSON malformati.
    
    Args:
        text: Testo della risposta di Claude
        
    Returns:
        Lista di dizionari con i link trovati
    """
    
    try:
        # Pulisci il testo
        text = text.strip()
        
        # Rimuovi markdown code blocks se presenti
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        print("🔍 Tentativo parsing JSON...")
        
        # Cerca il pattern JSON principale
        json_pattern = r'\{\s*"links"\s*:\s*\[.*?\]\s*\}'
        match = re.search(json_pattern, text, re.DOTALL)
        
        if not match:
            print("⚠️ Pattern JSON non trovato")
            # Prova estrazione manuale URL
            return extract_urls_manually(text)
        
        json_str = match.group(0)
        print(f"JSON estratto (primi 200 char): {json_str[:200]}")
        
        # Prova a fare il parse del JSON
        try:
            data = json.loads(json_str)
            links = data.get('links', [])
            
            if not isinstance(links, list):
                print("⚠️ 'links' non è una lista")
                return []
            
            # Valida e pulisci ogni link
            validated_links = []
            for link in links:
                if not isinstance(link, dict):
                    continue
                
                # Verifica campi obbligatori
                if 'url' not in link or not link['url']:
                    continue
                
                validated_link = {
                    'tipo_screening': link.get('tipo_screening', 'Screening oncologici'),
                    'url': link.get('url', '').strip(),
                    'nome_ente': link.get('nome_ente', 'Ente Sanitario'),
                    'note': link.get('note', 'Link per prenotazione screening')
                }
                
                # Verifica che l'URL sia valido
                if validated_link['url'].startswith('http'):
                    validated_links.append(validated_link)
            
            print(f"✅ {len(validated_links)} link validati")
            return validated_links
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Errore JSON parsing: {str(e)}")
            # Fallback: estrazione manuale
            return extract_urls_manually(json_str)
            
    except Exception as e:
        print(f"❌ Errore generico in extract_links: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def extract_urls_manually(text: str) -> list:
    """
    Estrae URL manualmente dal testo quando il JSON parsing fallisce.
    Fallback method per recuperare almeno gli URL.
    
    Args:
        text: Testo da cui estrarre URL
        
    Returns:
        Lista di dizionari con gli URL trovati
    """
    
    print("🔧 Tentativo estrazione manuale URL...")
    
    # Pattern per URL
    url_pattern = r'https?://[^\s\"\'\)]+(?:gov\.it|regione\.[a-z]+\.it|salute|sanita|screening|asl|cup)[^\s\"\'\)]*'
    
    urls = re.findall(url_pattern, text, re.IGNORECASE)
    
    if not urls:
        print("⚠️ Nessun URL trovato nell'estrazione manuale")
        return []
    
    print(f"🔗 Trovati {len(urls)} URL nell'estrazione manuale")
    
    links = []
    for url in urls[:3]:  # Massimo 3 URL
        # Pulisci l'URL
        url = url.rstrip('.,;)')
        
        links.append({
            'tipo_screening': 'Screening oncologici',
            'url': url,
            'nome_ente': 'Ente Sanitario Regionale',
            'note': 'Link per prenotazione screening (estratto automaticamente)'
        })
    
    return links