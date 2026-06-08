"""
ONE-DELUX-FAST - Serveur Complet Progressif
SOLITAIRE HACK - Architecture professionnelle

Version incrémentale qui intègre progressivement les modules
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import uvicorn

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

# Variables globales pour les services
api_client = None
data_manager = None
prediction_engine = None

# Modèles Pydantic pour les requêtes/réponses
class EventResponse(BaseModel):
    event_id: int
    sport_name: str
    league_name: str
    team1_name: str
    team2_name: str
    is_live: bool
    start_time: int
    favorite_team: Optional[str] = None
    current_score: Optional[str] = None

class PredictionResponse(BaseModel):
    event_id: int
    prediction_type: str
    predicted_value: str
    confidence: float
    probability_distribution: Optional[Dict[str, float]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    modules_loaded: Dict[str, bool]
    api_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

def init_services():
    """Initialise les services de manière progressive"""
    global api_client, data_manager, prediction_engine
    
    modules_status = {
        "api_client": False,
        "data_manager": False,
        "prediction_engine": False
    }
    
    # Tentative d'import et d'initialisation de l'API Client
    try:
        from one_delux_fast.api_client import get_api_client
        api_client = get_api_client()
        modules_status["api_client"] = True
        logger.info("✅ Module API Client chargé avec succès")
    except Exception as e:
        logger.warning(f"⚠️ Impossible de charger le module API Client: {e}")
    
    # Tentative d'import et d'initialisation du Data Manager
    try:
        from one_delux_fast.data_manager import get_data_manager
        data_manager = get_data_manager()
        modules_status["data_manager"] = True
        logger.info("✅ Module Data Manager chargé avec succès")
    except Exception as e:
        logger.warning(f"⚠️ Impossible de charger le module Data Manager: {e}")
    
    # Tentative d'import et d'initialisation du Prediction Engine
    try:
        from one_delux_fast.prediction_engine import get_prediction_engine
        prediction_engine = get_prediction_engine()
        modules_status["prediction_engine"] = True
        logger.info("✅ Module Prediction Engine chargé avec succès")
    except Exception as e:
        logger.warning(f"⚠️ Impossible de charger le module Prediction Engine: {e}")
    
    return modules_status

# Initialiser les services au démarrage
modules_status = init_services()


@app.on_event("startup")
async def startup_event():
    """Événement de démarrage de l'application"""
    logger.info("🚀 ONE-DELUX-FAST Server démarré")
    logger.info(f"📦 Modules chargés: {modules_status}")


@app.get("/")
async def root():
    """Route racine - informations sur l'API"""
    return {
        "name": "ONE-DELUX-FAST API",
        "version": "1.0.0",
        "status": "operational",
        "modules": modules_status,
        "documentation": "/docs",
        "message": "Serveur opérationnel avec modules progressifs"
    }


@app.get("/health")
async def health_check():
    """Vérification de santé du système"""
    api_requests = 0
    cache_hits = 0
    cache_misses = 0
    
    if api_client:
        stats = api_client.get_statistics()
        api_requests = stats.get('total_requests', 0)
    
    if data_manager:
        cache_stats = data_manager.cache.get_statistics()
        cache_hits = cache_stats.get('hits', 0)
        cache_misses = cache_stats.get('misses', 0)
    
    return HealthResponse(
        status="healthy" if all(modules_status.values()) else "degraded",
        timestamp=datetime.now().isoformat(),
        modules_loaded=modules_status,
        api_requests=api_requests,
        cache_hits=cache_hits,
        cache_misses=cache_misses
    )


@app.get("/events", response_model=List[EventResponse])
async def get_events(limit: int = 40, live_only: bool = False):
    """
    Récupère la liste des événements actuels
    - limit: nombre maximum d'événements à retourner
    - live_only: filtrer uniquement les événements en direct
    """
    if not api_client:
        raise HTTPException(status_code=503, detail="Module API Client non disponible")
    
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
            current_score = None
            if event.score and event.is_live:
                current_score = f"{event.score.team1_score}-{event.score.team2_score}"
            
            event_responses.append(EventResponse(
                event_id=event.event_id,
                sport_name=event.sport_name,
                league_name=event.league_name,
                team1_name=event.team1_name,
                team2_name=event.team2_name,
                is_live=event.is_live,
                start_time=event.start_time,
                favorite_team=event.get_favorite_team() if hasattr(event, 'get_favorite_team') else None,
                current_score=current_score
            ))
        
        return event_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des événements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/{event_id}")
async def get_event_details(event_id: int):
    """Récupère les détails d'un événement spécifique"""
    if not api_client:
        raise HTTPException(status_code=503, detail="Module API Client non disponible")
    
    try:
        response = api_client.get_events()
        
        if not response.is_valid():
            raise HTTPException(status_code=500, detail=response.error)
        
        events = response.data
        event = next((e for e in events if e.event_id == event_id), None)
        
        if not event:
            raise HTTPException(status_code=404, detail="Événement non trouvé")
        
        return event.to_dict() if hasattr(event, 'to_dict') else {
            "event_id": event.event_id,
            "team1_name": event.team1_name,
            "team2_name": event.team2_name,
            "is_live": event.is_live
        }
        
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
    if not api_client or not prediction_engine:
        raise HTTPException(status_code=503, detail="Modules requis non disponibles")
    
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
            prediction_type=prediction.prediction_type.value if hasattr(prediction.prediction_type, 'value') else str(prediction.prediction_type),
            predicted_value=prediction.predicted_value,
            confidence=prediction.confidence,
            probability_distribution=prediction.probability_distribution
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
    if not api_client or not prediction_engine:
        raise HTTPException(status_code=503, detail="Modules requis non disponibles")
    
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
    if not api_client or not prediction_engine:
        raise HTTPException(status_code=503, detail="Modules requis non disponibles")
    
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
                "model_version": getattr(prediction, 'model_version', 'unknown')
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
    if not api_client or not data_manager:
        raise HTTPException(status_code=503, detail="Modules requis non disponibles")
    
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
    api_stats = {"total_requests": 0, "total_errors": 0, "success_rate": 0.0}
    cache_stats = {"cache_size": 0, "hits": 0, "misses": 0, "hit_rate": 0.0}
    
    if api_client:
        api_stats = api_client.get_statistics()
    
    if data_manager:
        cache_stats = data_manager.cache.get_statistics()
    
    return {
        "api": api_stats,
        "cache": cache_stats,
        "modules": modules_status,
        "system": {
            "timestamp": datetime.now().isoformat(),
            "status": "operational" if all(modules_status.values()) else "degraded"
        }
    }


@app.delete("/cache")
async def clear_cache():
    """Vide le cache"""
    if not data_manager:
        raise HTTPException(status_code=503, detail="Module Data Manager non disponible")
    
    data_manager.cache.clear()
    return {
        "status": "success",
        "message": "Cache vidé avec succès"
    }


@app.get("/modules")
async def get_modules_status():
    """Retourne le statut des modules chargés"""
    return {
        "modules": modules_status,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Démarrage du serveur ONE-DELUX-FAST avec modules progressifs")
    uvicorn.run(
        "enhanced_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )