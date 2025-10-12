from langchain_anthropic import ChatAnthropic
import os
import json
import re

def get_available_screenings(eta: int, sesso: str) -> list:
    """Determina quali screening sono disponibili in base a età e sesso"""
    screenings = []
    
    if sesso == 'F' and 50 <= eta <= 69:
        screenings.append({'tipo_screening': 'Mammografia', 'descrizione': 'Screening tumore della mammella'})
    
    if sesso == 'F' and 25 <= eta <= 64:
        screenings.append({'tipo_screening': 'Pap-test', 'descrizione': 'Screening tumore del collo dell\'utero'})
    
    if 50 <= eta <= 74:
        screenings.append({'tipo_screening': 'Test sangue occulto fecale', 'descrizione': 'Screening tumore del colon-retto'})
    
    return screenings

async def run_screening_agent(eta: int, sesso: str, regione: str, comune: str) -> list:
    """Esegue l'agente AI per trovare link di prenotazione screening."""
    
    print(f"🤖 Avvio agente per: {eta} anni, {sesso}, {comune}, {regione}")
    
    screening_list = get_available_screenings(eta, sesso)
    
    if not screening_list:
        print("⚠️ Nessuno screening disponibile")
        return []
    
    print(f"📋 Screening da cercare: {[s['tipo_screening'] for s in screening_list]}")
    
    # Inizializza Claude
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=0.2,
        max_tokens=4096,
        anthropic_api_key=os.getenv("CLAUDE_API_KEY")
    )
    
    # Crea prompt dettagliato
    screening_names = ", ".join([s['tipo_screening'] for s in screening_list])
    
    prompt_text = f"""Sei un assistente esperto nel trovare link di prenotazione per screening oncologici del Sistema Sanitario Nazionale italiano.

TASK: Trova i link UFFICIALI e DIRETTI per prenotare i seguenti screening:
- Screening: {screening_names}
- Regione: {regione}
- Comune: {comune}

Cerca su internet i seguenti siti:
1. Portale ufficiale della Regione {regione} per screening oncologici
2. Sito dell'ASL di {comune}
3. CUP online {regione} (Centro Unico Prenotazioni)
4. Portali di prenotazione screening {screening_names} {comune}

RISPOSTA RICHIESTA in formato JSON:
{{
  "links": [
    {{
      "tipo_screening": "nome screening",
      "url": "https://...",
      "nome_ente": "Nome ASL o ente",
      "note": "Breve descrizione"
    }}
  ]
}}

IMPORTANTE: 
- Includi SOLO link a siti ufficiali (.gov.it, ASL, Regioni, sanita.regione.it)
- NON inventare link
- Se non trovi link validi, restituisci {{"links": []}}
- Restituisci SOLO il JSON, nessun altro testo
"""
    
    try:
        print("🔍 Invio richiesta a Claude...")
        
        response = await llm.ainvoke(prompt_text)
        output_text = response.content if hasattr(response, 'content') else str(response)
        
        print(f"✅ Risposta ricevuta: {output_text[:300]}...")
        
        links = extract_json_from_output(output_text)
        print(f"🔗 Link estratti: {len(links)}")
        
        return links
        
    except Exception as e:
        print(f"❌ Errore agente: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def extract_json_from_output(text: str) -> list:
    """Estrae array di link da risposta Claude"""
    try:
        # Cerca pattern JSON
        json_match = re.search(r'\{[\s\S]*?"links"[\s\S]*?\}', text)
        
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            return data.get('links', [])
        
        return []
        
    except Exception as e:
        print(f"⚠️ Errore parsing JSON: {str(e)}")
        return []