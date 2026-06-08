"""
ONE-DELUX-FAST - Module Client API
SOLITAIRE HACK - Architecture professionnelle

Module de gestion des communications avec l'API 888starz
Implémente le pattern Singleton avec gestion d'erreurs robuste
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging
from functools import lru_cache


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BetType(Enum):
    """Énumération des types de paris disponibles"""
    TEAM2_WIN_OUTSIDER = 1
    TEAM1_WIN_OUTSIDER = 2
    TEAM1_WIN_FAVORITE = 3
    TEAM2_WIN_FAVORITE = 4
    DOUBLE_CHANCE_1X_12 = 5
    DOUBLE_CHANCE_X2_12 = 6
    HANDICAP_POSITIVE_TEAM1 = 7
    HANDICAP_NEGATIVE_TEAM1 = 8
    OVER_POINTS = 9
    UNDER_POINTS = 10
    TEAM1_OVER = 11
    TEAM1_UNDER = 12
    TEAM2_OVER = 13
    TEAM2_UNDER = 14
    
    @classmethod
    def get_description(cls, code: int) -> str:
        """Retourne la description d'un type de pari"""
        descriptions = {
            1: "Victoire Équipe 2 (Outsider)",
            2: "Victoire Équipe 1 (Outsider)",
            3: "Victoire Équipe 1 (Favorite)",
            4: "Victoire Équipe 2 (Favorite)",
            5: "Double Chance 1X ou 12",
            6: "Double Chance X2 ou 12",
            7: "Handicap Positif Équipe 1",
            8: "Handicap Négatif Équipe 1",
            9: "Over (Plus de buts/points)",
            10: "Under (Moins de buts/points)",
            11: "Équipe 1 marque plus de",
            12: "Équipe 1 marque moins de",
            13: "Équipe 2 marque plus de",
            14: "Équipe 2 marque moins de"
        }
        return descriptions.get(code, "Type inconnu")


@dataclass
class OddsInfo:
    """Informations sur une cote"""
    bet_type: int
    coefficient: float
    coefficient_str: str
    parameter: Optional[float] = None
    group: Optional[int] = None
    
    def __post_init__(self):
        """Validation des données après initialisation"""
        if self.coefficient <= 0:
            raise ValueError("Le coefficient doit être positif")


@dataclass
class ScoreInfo:
    """Informations sur le score"""
    team1_score: int
    team2_score: int
    time_seconds: int
    status: str
    is_final: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return asdict(self)


@dataclass
class Event:
    """Représente un événement sportif"""
    event_id: int
    sport_id: int
    sport_name: str
    league_id: int
    league_name: str
    team1_id: int
    team1_name: str
    team2_id: int
    team2_name: str
    start_time: int
    is_live: bool
    score: Optional[ScoreInfo]
    odds: List[OddsInfo]
    additional_odds: List[OddsInfo]
    country: str
    last_update: int
    
    def __post_init__(self):
        """Validation des données après initialisation"""
        if self.event_id <= 0:
            raise ValueError("L'ID d'événement doit être positif")
        if not self.team1_name or not self.team2_name:
            raise ValueError("Les noms d'équipes ne peuvent pas être vides")
    
    def get_main_odds(self, bet_type: int) -> Optional[OddsInfo]:
        """Retourne les cotes principales pour un type donné"""
        for odds in self.odds:
            if odds.bet_type == bet_type:
                return odds
        return None
    
    def get_favorite_team(self) -> str:
        """Détermine l'équipe favorite basée sur les cotes 1X2"""
        odds_1 = self.get_main_odds(3)  # Victoire équipe 1 favorite
        odds_2 = self.get_main_odds(4)  # Victoire équipe 2 favorite
        
        if odds_1 and odds_2:
            if odds_1.coefficient < odds_2.coefficient:
                return self.team1_name
            else:
                return self.team2_name
        
        return "Inconnu"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'événement en dictionnaire"""
        return {
            'event_id': self.event_id,
            'sport_name': self.sport_name,
            'league_name': self.league_name,
            'team1_name': self.team1_name,
            'team2_name': self.team2_name,
            'start_time': self.start_time,
            'is_live': self.is_live,
            'score': self.score.to_dict() if self.score else None,
            'odds_count': len(self.odds),
            'additional_odds_count': len(self.additional_odds),
            'favorite_team': self.get_favorite_team(),
            'last_update': self.last_update
        }


class APIResponse:
    """Conteneur pour la réponse API avec métadonnées"""
    
    def __init__(self, success: bool, data: Any, error: str = "", error_code: int = 0):
        self.success = success
        self.data = data
        self.error = error
        self.error_code = error_code
        self.timestamp = datetime.now()
    
    def is_valid(self) -> bool:
        """Vérifie si la réponse est valide"""
        return self.success and self.error_code == 0


class APIClientConfig:
    """Configuration du client API"""
    
    def __init__(self):
        self.base_url = "https://888starz.bet/service-api/LiveFeed/Get1x2_VZip"
        self.timeout = 10
        self.max_retries = 3
        self.retry_delay = 2
        self.default_params = {
            'sports': '85',
            'count': '80',
            'lng': 'fr',
            'gr': '789',
            'mode': '4',
            'country': '96',
            'partner': '233',
            'getEmpty': 'true',
            'virtualSports': 'true',
            'noFilterBlockEvent': 'true'
        }


class APIClient:
    """
    Client API professionnel pour 888starz
    Implémente le pattern Singleton avec retry logic
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Implémente le pattern Singleton"""
        if cls._instance is None:
            cls._instance = super(APIClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialise le client API"""
        if not APIClient._initialized:
            self.config = APIClientConfig()
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            })
            self._request_count = 0
            self._error_count = 0
            APIClient._initialized = True
            logger.info("Client API initialisé")
    
    def _make_request(self, params: Dict[str, str]) -> APIResponse:
        """
        Effectue une requête HTTP avec retry logic
        Retourne un objet APIResponse
        """
        self._request_count += 1
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Tentative {attempt + 1}/{self.config.max_retries}")
                
                response = self.session.get(
                    self.config.base_url,
                    params=params,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Vérifier les métadonnées de réponse
                        if not data.get('Success', False):
                            error_msg = data.get('Error', 'Erreur inconnue')
                            error_code = data.get('ErrorCode', 0)
                            logger.warning(f"Erreur API: {error_msg} (code: {error_code})")
                            return APIResponse(False, None, error_msg, error_code)
                        
                        logger.info(f"Requête réussie (status: {response.status_code})")
                        return APIResponse(True, data)
                    
                    except json.JSONDecodeError as e:
                        logger.error(f"Erreur de décodage JSON: {e}")
                        return APIResponse(False, None, "JSON décodage erreur", 500)
                
                else:
                    logger.warning(f"Status code non-200: {response.status_code}")
                    if attempt < self.config.max_retries - 1:
                        time.sleep(self.config.retry_delay)
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout après {self.config.timeout}s")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur de requête: {e}")
                self._error_count += 1
                return APIResponse(False, None, str(e), 500)
        
        self._error_count += 1
        return APIResponse(False, None, "Max retries atteint", 503)
    
    def get_events(self, **kwargs) -> APIResponse:
        """
        Récupère les événements depuis l'API
        kwargs: paramètres optionnels pour surcharger les défauts
        """
        params = self.config.default_params.copy()
        params.update(kwargs)
        
        logger.info(f"Récupération des événements avec params: {params}")
        api_response = self._make_request(params)
        
        if api_response.is_valid():
            try:
                events = self._parse_events(api_response.data)
                api_response.data = events
                logger.info(f"{len(events)} événements parsés avec succès")
            except Exception as e:
                logger.error(f"Erreur lors du parsing: {e}")
                api_response = APIResponse(False, None, str(e), 500)
        
        return api_response
    
    def _parse_events(self, data: Dict) -> List[Event]:
        """Parse les données brutes en objets Event"""
        events = []
        
        for event_data in data.get('Value', []):
            try:
                # Parser les informations de score
                score = self._parse_score(event_data.get('SC', {}))
                
                # Parser les cotes principales
                odds = self._parse_odds(event_data.get('E', []))
                
                # Parser les cotes additionnelles
                additional_odds = self._parse_additional_odds(event_data.get('AE', []))
                
                event = Event(
                    event_id=event_data.get('I', 0),
                    sport_id=event_data.get('SI', 0),
                    sport_name=event_data.get('SN', 'Unknown'),
                    league_id=event_data.get('LI', 0),
                    league_name=event_data.get('L', 'Unknown'),
                    team1_id=event_data.get('O1I', 0),
                    team1_name=event_data.get('O1', 'Unknown'),
                    team2_id=event_data.get('O2I', 0),
                    team2_name=event_data.get('O2', 'Unknown'),
                    start_time=event_data.get('S', 0),
                    is_live=event_data.get('ICY', False),
                    score=score,
                    odds=odds,
                    additional_odds=additional_odds,
                    country=event_data.get('CE', 'Unknown'),
                    last_update=event_data.get('U', 0)
                )
                events.append(event)
                
            except Exception as e:
                logger.warning(f"Erreur lors du parsing de l'événement: {e}")
                continue
        
        return events
    
    def _parse_score(self, score_data: Dict) -> Optional[ScoreInfo]:
        """Parse les données de score"""
        if not score_data:
            return None
        
        final_score = score_data.get('FS', {})
        
        return ScoreInfo(
            team1_score=final_score.get('S1', 0),
            team2_score=final_score.get('S2', 0),
            time_seconds=score_data.get('TS', 0),
            status=score_data.get('SLS', 'Unknown'),
            is_final=score_data.get('I', '') == 'Final'
        )
    
    def _parse_odds(self, odds_data: List[Dict]) -> List[OddsInfo]:
        """Parse les cotes principales"""
        odds = []
        
        for odd_data in odds_data:
            try:
                odds_info = OddsInfo(
                    bet_type=odd_data.get('T', 0),
                    coefficient=odd_data.get('C', 0.0),
                    coefficient_str=odd_data.get('CV', ''),
                    parameter=odd_data.get('P'),
                    group=odd_data.get('G')
                )
                odds.append(odds_info)
            except Exception as e:
                logger.warning(f"Erreur lors du parsing d'une cote: {e}")
                continue
        
        return odds
    
    def _parse_additional_odds(self, additional_data: List[Dict]) -> List[OddsInfo]:
        """Parse les cotes additionnelles (handicaps)"""
        odds = []
        
        for group_data in additional_data:
            for market_data in group_data.get('ME', []):
                try:
                    odds_info = OddsInfo(
                        bet_type=market_data.get('T', 0),
                        coefficient=market_data.get('C', 0.0),
                        coefficient_str=market_data.get('CV', ''),
                        parameter=market_data.get('P'),
                        group=group_data.get('G')
                    )
                    odds.append(odds_info)
                except Exception as e:
                    logger.warning(f"Erreur lors du parsing d'une cote additionnelle: {e}")
                    continue
        
        return odds
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du client"""
        return {
            'total_requests': self._request_count,
            'total_errors': self._error_count,
            'success_rate': (self._request_count - self._error_count) / self._request_count if self._request_count > 0 else 0
        }
    
    def reset_statistics(self) -> None:
        """Réinitialise les statistiques"""
        self._request_count = 0
        self._error_count = 0
        logger.info("Statistiques réinitialisées")


# Instance globale du client API
api_client = APIClient()


def get_api_client() -> APIClient:
    """Retourne l'instance singleton du client API"""
    return api_client