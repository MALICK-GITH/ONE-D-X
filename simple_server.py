"""
ONE-DELUX-FAST - Serveur Simplifié de Test
SOLITAIRE HACK
"""

from fastapi import FastAPI

app = FastAPI(title="ONE-DELUX-FAST Test Server")

@app.get("/")
async def root():
    return {
        "message": "ONE-DELUX-FAST Server is running!",
        "status": "operational"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)