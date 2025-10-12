from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from agent.orchestrator import run_screening_agent

load_dotenv()

app = FastAPI(title="Prevenzia Agent API")

# CORS per permettere chiamate da prevenzia.eu
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://prevenzia.eu", "http://localhost", "https://www.prevenzia.eu"],
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
        print(f"📥 Ricevuta richiesta: {req.eta} anni, {req.sesso}, {req.comune}, {req.regione}")
        
        # Chiama DIRETTAMENTE l'agente AI
        links = await run_screening_agent(
            eta=req.eta,
            sesso=req.sesso,
            regione=req.regione,
            comune=req.comune
        )
        
        print(f"✅ Agente ha trovato {len(links) if links else 0} link")
        
        return {
            "success": True,
            "data": {
                "links_asl": links if links else [],
                "fonte": "agent_ai"
            },
            "message": "Ricerca completata"
        }
    
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)