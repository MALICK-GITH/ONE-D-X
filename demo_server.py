"""
ONE-DELUX-FAST - Serveur de Démonstration
SOLITAIRE HACK - Architecture professionnelle

Version de démonstration avec données simulées
Fonctionne sans dépendances ML complexes
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import random
import uvicorn
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title="ONE-DELUX-FAST API - Demo",
    description="API de prédiction sportive (Mode Démonstration)",
    version="1.0.0-demo"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Données de démonstration
DEMO_EVENTS = [
    {
        "event_id": 727086376,
        "sport_name": "FIFA",
        "league_name": "FC 26. 5x5 Rush. Superligue",
        "team1_name": "Olympique Lyonnais",
        "team2_name": "Arsenal",
        "is_live": True,
        "start_time": 1780735800,
        "favorite_team": "Arsenal",
        "current_score": "1-2"
    },
    {
        "event_id": 727090494,
        "sport_name": "FIFA",
        "league_name": "FC 26. 5x5 Rush. Superligue",
        "team2_name": "Roma",
        "team1_name": "Paris Saint-Germain",
        "is_live": False,
        "start_time": 1780737000,
        "favorite_team": "Paris Saint-Germain",
        "current_score": None
    },
    {
        "event_id": 727088467,
        "sport_name": "FIFA",
        "league_name": "FC 26. 5x5 Rush. Superligue",
        "team1_name": "PSV Eindhoven",
        "team2_name": "Real Madrid",
        "is_live": False,
        "start_time": 1780736400,
        "favorite_team": "Real Madrid",
        "current_score": None
    }
]

# Modèles Pydantic
class EventResponse(BaseModel):
    event_id: int
    sport_name: str
    league_name: str
    team1_name: str
    team2_name: str
    is_live: bool
    start_time: int
    favorite_team: Optional[str]
    current_score: Optional[str]

class PredictionResponse(BaseModel):
    event_id: int
    prediction_type: str
    predicted_value: str
    confidence: float
    probability_distribution: Dict[str, float]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    mode: str
    total_events: int


@app.get("/")
async def root():
    """Route racine"""
    return {
        "name": "ONE-DELUX-FAST API - Demo",
        "version": "1.0.0-demo",
        "status": "operational",
        "mode": "demonstration",
        "message": "Serveur de démonstration avec données simulées",
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """Vérification de santé"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        mode="demonstration",
        total_events=len(DEMO_EVENTS)
    )


@app.get("/events", response_model=List[EventResponse])
async def get_events(limit: int = 40, live_only: bool = False):
    """Récupère les événements (données de démonstration)"""
    events = DEMO_EVENTS.copy()
    
    if live_only:
        events = [e for e in events if e["is_live"]]
    
    return events[:limit]


@app.get("/events/{event_id}")
async def get_event_details(event_id: int):
    """Récupère les détails d'un événement"""
    event = next((e for e in DEMO_EVENTS if e["event_id"] == event_id), None)
    
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")
    
    return event


@app.get("/predictions/{event_id}", response_model=PredictionResponse)
async def get_prediction(event_id: int):
    """Génère une prédiction (simulation)"""
    event = next((e for e in DEMO_EVENTS if e["event_id"] == event_id), None)
    
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")
    
    # Simulation de prédiction
    confidence = round(random.uniform(0.6, 0.95), 2)
    team1_prob = round(confidence * random.uniform(0.4, 0.7), 3)
    team2_prob = round(1 - team1_prob, 3)
    draw_prob = round(1 - team1_prob - team2_prob, 3)
    
    predicted = "team1" if team1_prob > team2_prob else "team2"
    
    return PredictionResponse(
        event_id=event_id,
        prediction_type="match_winner",
        predicted_value=predicted,
        confidence=confidence,
        probability_distribution={
            "team1": team1_prob,
            "team2": team2_prob,
            "draw": max(0, draw_prob)
        }
    )


@app.get("/predictions/{event_id}/over-under")
async def get_over_under_prediction(event_id: int, threshold: float = 2.5):
    """Prédiction Over/Under (simulation)"""
    event = next((e for e in DEMO_EVENTS if e["event_id"] == event_id), None)
    
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")
    
    confidence = round(random.uniform(0.55, 0.85), 2)
    over_prob = round(random.uniform(0.3, 0.7), 3)
    under_prob = round(1 - over_prob, 3)
    
    predicted = "over" if over_prob > under_prob else "under"
    
    return {
        "event_id": event_id,
        "prediction_type": "over_under",
        "threshold": threshold,
        "predicted_value": predicted,
        "confidence": confidence,
        "probability_distribution": {
            "over": over_prob,
            "under": under_prob
        }
    }


@app.get("/predictions/{event_id}/all")
async def get_all_predictions(event_id: int):
    """Toutes les prédictions (simulation)"""
    event = next((e for e in DEMO_EVENTS if e["event_id"] == event_id), None)
    
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")
    
    # Simuler plusieurs prédictions
    return {
        "event_id": event_id,
        "event_name": f"{event['team1_name']} vs {event['team2_name']}",
        "mode": "demonstration",
        "predictions": {
            "match_winner": {
                "predicted_value": "team1" if random.random() > 0.5 else "team2",
                "confidence": round(random.uniform(0.6, 0.9), 2),
                "model_version": "demo_1.0.0"
            },
            "over_under_2.5": {
                "predicted_value": "over" if random.random() > 0.5 else "under",
                "confidence": round(random.uniform(0.55, 0.85), 2),
                "model_version": "demo_1.0.0"
            },
            "over_under_3.5": {
                "predicted_value": "over" if random.random() > 0.5 else "under",
                "confidence": round(random.uniform(0.5, 0.8), 2),
                "model_version": "demo_1.0.0"
            }
        }
    }


@app.get("/stats")
async def get_statistics():
    """Statistiques du système (simulation)"""
    return {
        "api": {
            "total_requests": random.randint(100, 500),
            "total_errors": 0,
            "success_rate": 1.0
        },
        "cache": {
            "cache_size": len(DEMO_EVENTS),
            "hits": random.randint(50, 200),
            "misses": random.randint(10, 50),
            "hit_rate": round(random.uniform(0.7, 0.9), 2)
        },
        "system": {
            "timestamp": datetime.now().isoformat(),
            "status": "operational",
            "mode": "demonstration"
        }
    }


@app.delete("/cache")
async def clear_cache():
    """Vide le cache (simulation)"""
    return {
        "status": "success",
        "message": "Cache vidé avec succès (mode démonstration)"
    }


@app.post("/refresh")
async def refresh_data():
    """Rafraîchit les données (simulation)"""
    return {
        "status": "refresh_started",
        "message": "Rafraîchissement simulé terminé avec succès"
    }


if __name__ == "__main__":
    logger.info("🚀 Démarrage du serveur ONE-DELUX-FAST (Mode Démonstration)")
    logger.info("📊 Utilisation de données simulées")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )