from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from agent.orchestrator import run_screening_agent
from db.models import get_local_screening, check_cache, save_to_cache

load_dotenv()

app = FastAPI(title="Prevenzia Agent API")

# CORS per permettere chiamate da prevenzia.eu
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://prevenzia.eu", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    eta: int
    sesso: str
    regione: str
    comune: str

@app.get("/")
async def root():
    return {"status": "Prevenzia Agent API is running", "version": "1.0"}

@app.post("/api/search_screening")
async def search_screening(req: SearchRequest):
    try:
        # 1. Query DB locale per screening disponibili
        screening = await get_local_screening(req.eta, req.sesso, req.regione)
        
        if not screening:
            return {
                "success": True,
                "data": {
                    "screening": [],
                    "links_asl": [],
                    "fonte": "database"
                },
                "message": "Nessuno screening disponibile per questi parametri"
            }
        
        # 2. Check cache
        cached_links = await check_cache(req.regione, req.comune, screening)
        
        if cached_links:
            return {
                "success": True,
                "data": {
                    "screening": screening,
                    "links_asl": cached_links,
                    "fonte": "cache",
                    "ai_attivo": True
                },
                "message": "Risultati da cache"
            }
        
        # 3. Nessun cache → avvia agente AI
        links = await run_screening_agent(
            regione=req.regione,
            comune=req.comune,
            screening_list=screening
        )
        
        # 4. Salva in cache
        if links:
            await save_to_cache(req.regione, req.comune, links)
        
        return {
            "success": True,
            "data": {
                "screening": screening,
                "links_asl": links,
                "fonte": "agent_ai",
                "ai_attivo": len(links) > 0
            },
            "message": "Ricerca completata"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)