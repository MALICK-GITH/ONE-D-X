"""
ONE-DELUX-FAST - Plateforme de Prédiction Sportive
SOLITAIRE HACK - Architecture Professionnelle

Package principal pour la plateforme de prédiction ONE-DELUX-FAST
Intègre tous les modules nécessaires pour l'analyse et la prédiction
"""

__version__ = "1.0.0"
__author__ = "SOLITAIRE HACK"
__description__ = "Plateforme professionnelle de prédiction sportive"

from .api_client import (
    APIClient,
    APIResponse,
    Event,
    OddsInfo,
    ScoreInfo,
    BetType,
    get_api_client
)
from .data_manager import (
    DataManager,
    CacheManager,
    DatabaseManager,
    get_data_manager
)
from .prediction_engine import (
    PredictionEngine,
    Prediction,
    PredictionType,
    MatchWinnerPredictor,
    OverUnderPredictor,
    FeatureExtractor,
    get_prediction_engine
)
from .csv_predictor import (
    CSVPredictor,
    get_csv_predictor
)
from .platform_predictor import (
    PlatformPredictionService,
    get_platform_prediction_service,
)

__all__ = [
    'APIClient',
    'APIResponse', 
    'Event',
    'OddsInfo',
    'ScoreInfo',
    'BetType',
    'get_api_client',
    'DataManager',
    'CacheManager',
    'DatabaseManager',
    'get_data_manager',
    'PredictionEngine',
    'Prediction',
    'PredictionType',
    'MatchWinnerPredictor',
    'OverUnderPredictor',
    'FeatureExtractor',
    'get_prediction_engine',
    'CSVPredictor',
    'get_csv_predictor',
    'PlatformPredictionService',
    'get_platform_prediction_service'
]
