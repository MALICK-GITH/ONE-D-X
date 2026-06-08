"""
ONE-DELUX-FAST - Configuration Principale
SOLITAIRE HACK - Architecture Professionnelle

Configuration centralisée pour toute la plateforme
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class APIConfig:
    """Configuration de l'API"""
    base_url: str = "https://888starz.bet/service-api/LiveFeed/Get1x2_VZip"
    timeout: int = 10
    max_retries: int = 3
    retry_delay: int = 2
    default_sports: str = "85"
    default_count: str = "40"
    language: str = "fr"
    
    # Paramètres par défaut
    default_params: Dict[str, str] = None
    
    def __post_init__(self):
        if self.default_params is None:
            self.default_params = {
                'sports': self.default_sports,
                'count': self.default_count,
                'lng': self.language,
                'gr': '789',
                'mode': '4',
                'country': '96',
                'partner': '233',
                'getEmpty': 'true',
                'virtualSports': 'true',
                'noFilterBlockEvent': 'true'
            }


@dataclass
class CacheConfig:
    """Configuration du cache"""
    default_ttl: int = 60  # secondes
    max_size: int = 1000
    cleanup_interval: int = 300  # secondes
    
    # TTL spécifiques par type de données
    events_ttl: int = 30
    odds_ttl: int = 15
    predictions_ttl: int = 120


@dataclass
class DatabaseConfig:
    """Configuration de la base de données"""
    path: str = "one_delux_fast.db"
    backup_interval: int = 3600  # secondes
    max_history_days: int = 30
    
    # Tables à créer
    tables: list = None
    
    def __post_init__(self):
        if self.tables is None:
            self.tables = ['events', 'scores', 'odds', 'predictions']


@dataclass
class PredictionConfig:
    """Configuration des modèles de prédiction"""
    enabled: bool = True
    update_interval: int = 300  # secondes
    confidence_threshold: float = 0.6
    
    # Types de paris à prédire
    prediction_types: list = None
    
    def __post_init__(self):
        if self.prediction_types is None:
            self.prediction_types = [
                'match_winner',
                'over_under',
                'handicap',
                'correct_score'
            ]


@dataclass
class LoggingConfig:
    """Configuration du logging"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "one_delux_fast.log"
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5


@dataclass
class MonitoringConfig:
    """Configuration du monitoring"""
    enabled: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 60  # secondes
    
    # Alertes
    alert_on_api_failure: bool = True
    alert_on_prediction_error: bool = True
    alert_on_database_error: bool = True


class Config:
    """
    Configuration principale de l'application
    Implémente le pattern Singleton
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not Config._initialized:
            # Chemins de base
            self.base_dir = Path(__file__).parent
            self.data_dir = self.base_dir / "data"
            self.logs_dir = self.base_dir / "logs"
            self.models_dir = self.base_dir / "models"
            
            # Créer les répertoires nécessaires
            self._create_directories()
            
            # Sous-configurations
            self.api = APIConfig()
            self.cache = CacheConfig()
            self.database = DatabaseConfig()
            self.prediction = PredictionConfig()
            self.logging = LoggingConfig()
            self.monitoring = MonitoringConfig()
            
            # Configuration de l'application
            self.app_name = "ONE-DELUX-FAST"
            self.app_version = "1.0.0"
            self.environment = os.getenv("ENVIRONMENT", "development")
            self.debug = self.environment == "development"

            # Appliquer automatiquement les variables d'environnement au démarrage.
            self.update_from_env()

            Config._initialized = True
    
    def _create_directories(self) -> None:
        """Crée les répertoires nécessaires"""
        directories = [self.data_dir, self.logs_dir, self.models_dir]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def is_development(self) -> bool:
        """Vérifie si on est en environnement de développement"""
        return self.environment == "development"
    
    def is_production(self) -> bool:
        """Vérifie si on est en environnement de production"""
        return self.environment == "production"
    
    def get_database_path(self) -> str:
        """Retourne le chemin complet de la base de données"""
        db_path = Path(self.database.path)
        if db_path.is_absolute():
            return str(db_path)
        return str(self.data_dir / db_path)
    
    def get_log_path(self) -> str:
        """Retourne le chemin complet du fichier de log"""
        return str(self.logs_dir / self.logging.file_path)
    
    def update_from_env(self) -> None:
        """Met à jour la configuration depuis les variables d'environnement"""
        # API
        if os.getenv("API_BASE_URL"):
            self.api.base_url = os.getenv("API_BASE_URL")
        if os.getenv("API_TIMEOUT"):
            self.api.timeout = int(os.getenv("API_TIMEOUT"))
        
        # Database
        if os.getenv("DB_PATH"):
            self.database.path = os.getenv("DB_PATH")
        
        # Logging
        if os.getenv("LOG_LEVEL"):
            self.logging.level = os.getenv("LOG_LEVEL")
        
        # Environment
        if os.getenv("ENVIRONMENT"):
            self.environment = os.getenv("ENVIRONMENT")
            self.debug = self.environment == "development"


# Instance globale de la configuration
config = Config()


def get_config() -> Config:
    """Retourne l'instance singleton de la configuration"""
    return config
