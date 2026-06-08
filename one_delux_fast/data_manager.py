"""
ONE-DELUX-FAST - Module Gestion des Données
SOLITAIRE HACK - Architecture professionnelle

Module de gestion des données avec cache, historique et traitement
Implémente des patterns de gestion d'état robustes
"""

import sqlite3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from threading import Lock
import logging
from typing import Callable

from .api_client import Event, OddsInfo, ScoreInfo, APIResponse
from config import get_config


logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Entrée de cache avec TTL"""
    data: Any
    timestamp: datetime
    ttl: int  # Time to live en secondes
    
    def is_expired(self) -> bool:
        """Vérifie si l'entrée est expirée"""
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl)


class CacheManager:
    """
    Gestionnaire de cache en mémoire avec thread-safety
    Utilise le pattern Singleton avec locking
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not CacheManager._initialized:
            self._cache: Dict[str, CacheEntry] = {}
            self._lock = Lock()
            self._hits = 0
            self._misses = 0
            CacheManager._initialized = True
            logger.info("CacheManager initialisé")
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache"""
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                logger.debug(f"Cache miss pour la clé: {key}")
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                logger.debug(f"Cache expiré pour la clé: {key}")
                return None
            
            self._hits += 1
            logger.debug(f"Cache hit pour la clé: {key}")
            return entry.data
    
    def set(self, key: str, data: Any, ttl: int = 60) -> None:
        """Stocke une valeur dans le cache"""
        with self._lock:
            entry = CacheEntry(
                data=data,
                timestamp=datetime.now(),
                ttl=ttl
            )
            self._cache[key] = entry
            logger.debug(f"Cache set pour la clé: {key} (TTL: {ttl}s)")
    
    def invalidate(self, key: str) -> None:
        """Invalide une entrée spécifique"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache invalidé pour la clé: {key}")
    
    def clear(self) -> None:
        """Vide tout le cache"""
        with self._lock:
            self._cache.clear()
            logger.info("Cache vidé")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                'cache_size': len(self._cache),
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'total_requests': total_requests
            }
    
    def cleanup_expired(self) -> int:
        """Nettoie les entrées expirées, retourne le nombre nettoyé"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"Nettoyage de {len(expired_keys)} entrées expirées")
            
            return len(expired_keys)


class DatabaseManager:
    """
    Gestionnaire de base de données SQLite pour le stockage persistant
    Gère l'historique des événements et des cotes
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_config().get_database_path()
        self._lock = Lock()
        self._init_database()
        logger.info(f"DatabaseManager initialisé avec {self.db_path}")
    
    def _init_database(self) -> None:
        """Initialise les tables de la base de données"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Table des événements
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER UNIQUE,
                    sport_id INTEGER,
                    sport_name TEXT,
                    league_id INTEGER,
                    league_name TEXT,
                    team1_id INTEGER,
                    team1_name TEXT,
                    team2_id INTEGER,
                    team2_name TEXT,
                    start_time INTEGER,
                    is_live BOOLEAN,
                    country TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des scores
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER,
                    team1_score INTEGER,
                    team2_score INTEGER,
                    time_seconds INTEGER,
                    status TEXT,
                    is_final BOOLEAN,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events (event_id)
                )
            """)
            
            # Table des cotes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS odds (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER,
                    bet_type INTEGER,
                    coefficient REAL,
                    parameter REAL,
                    group_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events (event_id)
                )
            """)
            
            # Table des prédictions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY,
                    event_id INTEGER,
                    prediction_type TEXT,
                    predicted_value REAL,
                    confidence REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events (event_id)
                )
            """)
            
            # Index pour optimiser les requêtes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_event_id ON events(event_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_scores_event_id ON scores(event_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_odds_event_id ON odds(event_id)")
            
            conn.commit()
            conn.close()
    
    def save_event(self, event: Event) -> bool:
        """Sauvegarde un événement dans la base de données"""
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Insérer ou mettre à jour l'événement
                cursor.execute("""
                    INSERT OR REPLACE INTO events 
                    (event_id, sport_id, sport_name, league_id, league_name, 
                     team1_id, team1_name, team2_id, team2_name, start_time, 
                     is_live, country, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id, event.sport_id, event.sport_name,
                    event.league_id, event.league_name, event.team1_id,
                    event.team1_name, event.team2_id, event.team2_name,
                    event.start_time, event.is_live, event.country,
                    datetime.now()
                ))
                
                # Sauvegarder le score si disponible
                if event.score:
                    cursor.execute("""
                        INSERT INTO scores 
                        (event_id, team1_score, team2_score, time_seconds, status, is_final)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        event.event_id, event.score.team1_score,
                        event.score.team2_score, event.score.time_seconds,
                        event.score.status, event.score.is_final
                    ))
                
                # Sauvegarder les cotes
                for odds in event.odds:
                    cursor.execute("""
                        INSERT INTO odds 
                        (event_id, bet_type, coefficient, parameter, group_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        event.event_id, odds.bet_type, odds.coefficient,
                        odds.parameter, odds.group
                    ))
                
                # Sauvegarder les cotes additionnelles
                for odds in event.additional_odds:
                    cursor.execute("""
                        INSERT INTO odds 
                        (event_id, bet_type, coefficient, parameter, group_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        event.event_id, odds.bet_type, odds.coefficient,
                        odds.parameter, odds.group
                    ))
                
                conn.commit()
                conn.close()
                logger.debug(f"Événement {event.event_id} sauvegardé")
                return True
                
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde de l'événement: {e}")
                return False
    
    def get_event_history(self, event_id: int, hours: int = 24) -> List[Dict]:
        """Récupère l'historique d'un événement"""
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                cursor.execute("""
                    SELECT * FROM odds 
                    WHERE event_id = ? AND timestamp >= ?
                    ORDER BY timestamp
                """, (event_id, cutoff_time))
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                conn.close()
                
                return [dict(zip(columns, row)) for row in rows]
                
            except Exception as e:
                logger.error(f"Erreur lors de la récupération de l'historique: {e}")
                return []
    
    def get_events_by_league(self, league_name: str, limit: int = 100) -> List[Dict]:
        """Récupère les événements par ligue"""
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM events 
                    WHERE league_name = ?
                    ORDER BY start_time DESC
                    LIMIT ?
                """, (league_name, limit))
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                conn.close()
                
                return [dict(zip(columns, row)) for row in rows]
                
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des événements: {e}")
                return []


class DataManager:
    """
    Gestionnaire principal des données
    Coordonne le cache et la base de données
    """
    
    def __init__(self):
        self.cache = CacheManager()
        self.database = DatabaseManager(get_config().get_database_path())
        logger.info("DataManager initialisé")
    
    def get_events_with_cache(
        self,
        force_refresh: bool = False,
        fetcher: Optional[Callable[[], Any]] = None,
    ) -> Optional[List[Event]]:
        """
        Récupère les événements avec cache
        force_refresh: ignore le cache et force le rafraîchissement
        fetcher: fonction de récupération personnalisée, utile pour les tests
        """
        cache_key = "events_current"
        
        if not force_refresh:
            cached_events = self.cache.get(cache_key)
            if cached_events:
                return cached_events
        
        if fetcher is None:
            try:
                from .api_client import get_api_client

                api_client = get_api_client()
                response = api_client.get_events()
            except Exception as exc:
                logger.warning("Impossible de récupérer les événements: %s", exc)
                return None
        else:
            try:
                response = fetcher()
            except Exception as exc:
                logger.warning("Fetcher personnalisé en échec: %s", exc)
                return None

        if isinstance(response, APIResponse):
            if not response.is_valid():
                logger.warning("Réponse invalide lors du chargement des événements: %s", response.error)
                return None
            events = response.data
        else:
            events = response

        if not isinstance(events, list):
            logger.warning("Le récupérateur d'événements n'a pas renvoyé de liste")
            return None

        self.cache.set(cache_key, events, get_config().cache.events_ttl)
        for event in events:
            self.database.save_event(event)

        return events
    
    def cache_events(self, events: List[Event], ttl: int = 60) -> None:
        """Met en cache les événements"""
        cache_key = "events_current"
        self.cache.set(cache_key, events, ttl)
        
        # Sauvegarder également en base de données
        for event in events:
            self.database.save_event(event)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques combinées"""
        cache_stats = self.cache.get_statistics()
        
        return {
            'cache': cache_stats,
            'database': {
                'path': self.database.db_path,
                'status': 'active'
            }
        }
    
    def cleanup(self) -> None:
        """Nettoie les ressources"""
        self.cache.cleanup_expired()
        logger.info("Nettoyage des données terminé")


# Instance globale du gestionnaire de données
data_manager = DataManager()


def get_data_manager() -> DataManager:
    """Retourne l'instance singleton du DataManager"""
    return data_manager
