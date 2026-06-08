"""
ONE-DELUX-FAST - Serveur API Web
SOLITAIRE HACK - Architecture professionnelle

Serveur FastAPI pour l'interface web de la plateforme
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging
import uvicorn

from one_delux_fast import (
    get_api_client,
    get_data_manager,
    get_prediction_engine
)


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title="ONE-DELUX-FAST API",
    description="API de prédiction sportive professionnelle",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic pour les requêtes/réponses
class EventResponse(BaseModel):
    event_id: int
    sport_name: str
    league_name: str
    team1_name: str
    team2_name: str
    is_live: bool
    start_time: int
    favorite_team: str

class PredictionResponse(BaseModel):
    event_id: int
    prediction_type: str
    predicted_value: str
    confidence: float
    probability_distribution: dict

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    api_requests: int
    cache_hits: int
    cache_misses: int

# Initialisation des services
api_client = get_api_client()
data_manager = get_data_manager()
prediction_engine = get_prediction_engine()


@app.get("/")
async def root():
    """Route racine - informations sur l'API"""
    return {
        "name": "ONE-DELUX-FAST API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """Vérification de santé du système"""
    api_stats = api_client.get_statistics()
    cache_stats = data_manager.cache.get_statistics()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        api_requests=api_stats['total_requests'],
        cache_hits=cache_stats['hits'],
        cache_misses=cache_stats['misses']
    )


@app.get("/events", response_model=List[EventResponse])
async def get_events(limit: int = 40, live_only: bool = False):
    """
    Récupère la liste des événements actuels
    - limit: nombre maximum d'événements à retourner
    - live_only: filtrer uniquement les événements en direct
    """
    try:
        response = api_client.get_events()
        
        if not response.is_valid():
            raise HTTPException(status_code=500, detail=response.error)
        
        events = response.data
        
        if live_only:
            events = [e for e in events if e.is_live]
        
        events = events[:limit]
        
        # Convertir en format de réponse
        event_responses = []
        for event in events:
            event_responses.append(EventResponse(
                event_id=event.event_id,
                sport_name=event.sport_name,
                league_name=event.league_name,
                team1_name=event.team1_name,
                team2_name=event.team2_name,
                is_live=event.is_live,
                start_time=event.start_time,
                favorite_team=event.get_favorite_team()
            ))
        
        return event_responses
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des événements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/{event_id}")
async def get_event_details(event_id: int):
    """Récupère les détails d'un événement spécifique"""
    try:
        response = api_client.get_events()
        
        if not response.is_valid():
            raise HTTPException(status_code=500, detail=response.error)
        
        events = response.data
        event = next((e for e in events if e.event_id == event_id), None)
        
        if not event:
            raise HTTPException(status_code=404, detail="Événement non trouvé")
        
        return event.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des détails: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictions/{event_id}", response_model=PredictionResponse)
async def get_prediction(event_id: int):
    """
    Génère une prédiction pour un événement spécifique
    Retourne la prédiction du vainqueur avec confiance
    """
    try:
        response = api_client.get_events()
        
        if not response.is_valid():
            raise HTTPException(status_code=500, detail=response.error)
        
        events = response.data
        event = next((e for e in events if e.event_id == event_id), None)
        
        if not event:
            raise HTTPException(status_code=404, detail="Événement non trouvé")
        
        # Générer la prédiction
        prediction = prediction_engine.predict_match(event)
        
        return PredictionResponse(
            event_id=event.event_id,
            prediction_type=prediction.prediction_type.value,
            predicted_value=prediction.predicted_value,
            confidence=prediction.confidence,
            probability_distribution=prediction.probability_distribution or {}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la prédiction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictions/{event_id}/over-under")
async def get_over_under_prediction(event_id: int, threshold: float = 2.5):
    """
    Génère une prédiction Over/Under pour un événement
    - threshold: seuil pour la prédiction (défaut: 2.5)
    """
    try:
        response = api_client.get_events()
        
        if not response.is_valid():
            raise HTTPException(status_code=500, detail=response.error)
        
        events = response.data
        event = next((e for e in events if e.event_id == event_id), None)
        
        if not event:
            raise HTTPException(status_code=404, detail="Événement non trouvé")
        
        # Générer la prédiction Over/Under
        prediction = prediction_engine.predict_over_under(event, threshold)
        
        return {
            "event_id": event.event_id,
            "prediction_type": "over_under",
            "threshold": threshold,
            "predicted_value": prediction.predicted_value,
            "confidence": prediction.confidence,
            "probability_distribution": prediction.probability_distribution
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la prédiction Over/Under: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictions/{event_id}/all")
async def get_all_predictions(event_id: int):
    """
    Génère toutes les prédictions disponibles pour un événement
    """
    try:
        response = api_client.get_events()
        
        if not response.is_valid():
            raise HTTPException(status_code=500, detail=response.error)
        
        events = response.data
        event = next((e for e in events if e.event_id == event_id), None)
        
        if not event:
            raise HTTPException(status_code=404, detail="Événement non trouvé")
        
        # Générer toutes les prédictions
        predictions = prediction_engine.predict_all(event)
        
        result = {
            "event_id": event.event_id,
            "event_name": f"{event.team1_name} vs {event.team2_name}",
            "predictions": {}
        }
        
        for pred_type, prediction in predictions.items():
            result["predictions"][pred_type] = {
                "predicted_value": prediction.predicted_value,
                "confidence": prediction.confidence,
                "probability_distribution": prediction.probability_distribution,
                "model_version": prediction.model_version
            }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la génération des prédictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refresh")
async def refresh_data(background_tasks: BackgroundTasks):
    """
    Rafraîchit les données depuis l'API
    Opération asynchrone en arrière-plan
    """
    def refresh_task():
        try:
            response = api_client.get_events()
            if response.is_valid():
                data_manager.cache_events(response.data, ttl=60)
                logger.info("Données rafraîchies avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du rafraîchissement: {e}")
    
    background_tasks.add_task(refresh_task)
    
    return {
        "status": "refresh_started",
        "message": "Le rafraîchissement des données a été lancé en arrière-plan"
    }


@app.get("/stats")
async def get_statistics():
    """Retourne les statistiques du système"""
    api_stats = api_client.get_statistics()
    cache_stats = data_manager.cache.get_statistics()
    
    return {
        "api": {
            "total_requests": api_stats['total_requests'],
            "total_errors": api_stats['total_errors'],
            "success_rate": api_stats['success_rate']
        },
        "cache": {
            "cache_size": cache_stats['cache_size'],
            "hits": cache_stats['hits'],
            "misses": cache_stats['misses'],
            "hit_rate": cache_stats['hit_rate']
        },
        "system": {
            "timestamp": datetime.now().isoformat(),
            "status": "operational"
        }
    }


@app.delete("/cache")
async def clear_cache():
    """Vide le cache"""
    data_manager.cache.clear()
    return {
        "status": "success",
        "message": "Cache vidé avec succès"
    }


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Démarre le serveur FastAPI
    - host: adresse d'écoute (défaut: 0.0.0.0)
    - port: port d'écoute (défaut: 8000)
    - reload: auto-reload en mode développement
    """
    logger.info(f"🚀 Démarrage du serveur ONE-DELUX-FAST sur {host}:{port}")
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    start_server(host="0.0.0.0", port=8000, reload=True)