from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.utils.function_calling import convert_to_openai_function
from agent.tools.brave_search import brave_search
from agent.tools.web_scraper import scrape_page
from agent.tools.link_validator import validate_link
from agent.prompts import AGENT_SYSTEM_PROMPT, create_agent_prompt
import os
import json
import re

def get_available_screenings(eta: int, sesso: str) -> list:
    """Determina quali screening sono disponibili in base a età e sesso"""
    screenings = []
    
    # Mammografia
    if sesso == 'F' and 50 <= eta <= 69:
        screenings.append({
            'tipo_screening': 'Mammografia',
            'descrizione': 'Screening tumore della mammella'
        })
    
    # Pap-test
    if sesso == 'F' and 25 <= eta <= 64:
        screenings.append({
            'tipo_screening': 'Pap-test',
            'descrizione': 'Screening tumore del collo dell\'utero'
        })
    
    # Colon-retto
    if 50 <= eta <= 74:
        screenings.append({
            'tipo_screening': 'Test sangue occulto fecale',
            'descrizione': 'Screening tumore del colon-retto'
        })
    
    return screenings

async def run_screening_agent(eta: int, sesso: str, regione: str, comune: str) -> list:
    """Esegue l'agente AI per trovare link di prenotazione screening."""
    
    print(f"🤖 Avvio agente per: {eta} anni, {sesso}, {comune}, {regione}")
    
    # Determina screening disponibili
    screening_list = get_available_screenings(eta, sesso)
    
    if not screening_list:
        print("⚠️ Nessuno screening disponibile per questi parametri")
        return []
    
    print(f"📋 Screening da cercare: {[s['tipo_screening'] for s in screening_list]}")
    
    # Inizializza Claude
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=0.2,
        max_tokens=4096,
        anthropic_api_key=os.getenv("CLAUDE_API_KEY")
    )
    
    # Tools disponibili
    tools = [brave_search, scrape_page, validate_link]
    
    # Converti tools in formato OpenAI
    llm_with_tools = llm.bind(functions=[convert_to_openai_function(t) for t in tools])
    
    # Crea prompt
    screening_names = ", ".join([s['tipo_screening'] for s in screening_list])
    user_input = create_agent_prompt(screening_names, regione, comune)
    
    print(f"📝 Prompt creato: {user_input[:200]}...")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", AGENT_SYSTEM_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    # Crea agent chain
    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_to_openai_function_messages(x["intermediate_steps"])
        }
        | prompt
        | llm_with_tools
        | OpenAIFunctionsAgentOutputParser()
    )
    
    # Executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=15,
        handle_parsing_errors=True
    )
    
    # Esegui agente
    try:
        print("🔍 Esecuzione agente in corso...")
        result = await agent_executor.ainvoke({"input": user_input})
        output_text = result.get('output', '')
        
        print(f"✅ Agente completato. Output: {output_text[:200]}...")
        
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
        json_match = re.search(r'\{[\s\S]*"links"[\s\S]*\}', text)
        
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            return data.get('links', [])
        
        return []
        
    except json.JSONDecodeError:
        print("⚠️ Errore parsing JSON dalla risposta")
        return []