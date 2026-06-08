"""
ONE-DELUX-FAST - Moteur de Prédiction
SOLITAIRE HACK - Architecture professionnelle

Module de prédiction utilisant des modèles de Machine Learning
Implémente des modèles basés sur les cotes et l'historique
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
import pickle
from pathlib import Path

# ML imports
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

from .api_client import Event, OddsInfo


logger = logging.getLogger(__name__)


class PredictionType(Enum):
    """Types de prédictions disponibles"""
    MATCH_WINNER = "match_winner"
    OVER_UNDER = "over_under"
    HANDICAP = "handicap"
    CORRECT_SCORE = "correct_score"


@dataclass
class Prediction:
    """Résultat d'une prédiction"""
    event_id: int
    prediction_type: PredictionType
    predicted_value: Any
    confidence: float  # 0.0 à 1.0
    probability_distribution: Optional[Dict[str, float]] = None
    features_used: Optional[List[str]] = None
    model_version: str = "1.0.0"
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("La confiance doit être entre 0.0 et 1.0")


class FeatureExtractor:
    """
    Extracteur de caractéristiques pour les modèles ML
    Transforme les données brutes en features utilisables
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def extract_basic_features(self, event: Event) -> Dict[str, float]:
        """Extrait les caractéristiques de base d'un événement"""
        features = {}
        
        # Informations de base
        features['event_id'] = event.event_id
        features['sport_id'] = event.sport_id
        features['league_id'] = event.league_id
        features['is_live'] = 1.0 if event.is_live else 0.0
        
        # Score actuel si disponible
        if event.score:
            features['team1_score'] = event.score.team1_score
            features['team2_score'] = event.score.team2_score
            features['score_difference'] = event.score.team1_score - event.score.team2_score
            features['time_seconds'] = event.score.time_seconds
        else:
            features['team1_score'] = 0.0
            features['team2_score'] = 0.0
            features['score_difference'] = 0.0
            features['time_seconds'] = 0.0
        
        return features
    
    def extract_odds_features(self, event: Event) -> Dict[str, float]:
        """Extrait les caractéristiques des cotes"""
        features = {}
        
        # Cotes 1X2 principales
        odds_1 = event.get_main_odds(1)  # Équipe 2 outsider
        odds_2 = event.get_main_odds(2)  # Équipe 1 outsider
        odds_3 = event.get_main_odds(3)  # Équipe 1 favorite
        odds_4 = event.get_main_odds(4)  # Équipe 2 favorite
        
        # Utiliser les cotes favorites si disponibles
        team1_odds = odds_3.coefficient if odds_3 else (odds_2.coefficient if odds_2 else 2.0)
        team2_odds = odds_4.coefficient if odds_4 else (odds_1.coefficient if odds_1 else 2.0)
        
        features['team1_odds'] = team1_odds
        features['team2_odds'] = team2_odds
        features['odds_ratio'] = team1_odds / team2_odds if team2_odds > 0 else 1.0
        
        # Probabilités implicites (avec marge)
        total_prob = (1/team1_odds + 1/team2_odds)
        features['team1_implied_prob'] = (1/team1_odds) / total_prob if total_prob > 0 else 0.5
        features['team2_implied_prob'] = (1/team2_odds) / total_prob if total_prob > 0 else 0.5
        
        # Over/Under
        for odds in event.odds:
            if odds.bet_type == 9 and odds.parameter:  # Over
                features[f'over_{odds.parameter}'] = odds.coefficient
            elif odds.bet_type == 10 and odds.parameter:  # Under
                features[f'under_{odds.parameter}'] = odds.coefficient
        
        return features
    
    def extract_all_features(self, event: Event) -> Dict[str, float]:
        """Extrait toutes les caractéristiques disponibles"""
        features = {}
        features.update(self.extract_basic_features(event))
        features.update(self.extract_odds_features(event))
        return features


class BaseModel:
    """
    Classe de base pour tous les modèles de prédiction
    Définit l'interface commune
    """
    
    def __init__(self, model_type: str):
        self.model_type = model_type
        self.model = None
        self.feature_extractor = FeatureExtractor()
        self.is_trained = False
        self.model_version = "1.0.0"
    
    def train(self, events: List[Event], outcomes: List[Any]) -> None:
        """
        Entraîne le modèle sur des données historiques
        events: Liste des événements
        outcomes: Résultats correspondants
        """
        raise NotImplementedError("La méthode train doit être implémentée par les sous-classes")
    
    def predict(self, event: Event) -> Prediction:
        """
        Génère une prédiction pour un événement
        event: Événement à prédire
        """
        raise NotImplementedError("La méthode predict doit être implémentée par les sous-classes")
    
    def save_model(self, path: str) -> None:
        """Sauvegarde le modèle sur disque"""
        if self.model is None:
            raise ValueError("Aucun modèle à sauvegarder")
        
        model_data = {
            'model': self.model,
            'model_type': self.model_type,
            'is_trained': self.is_trained,
            'model_version': self.model_version,
            'feature_extractor': self.feature_extractor
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Modèle sauvegardé dans {path}")
    
    def load_model(self, path: str) -> None:
        """Charge un modèle depuis disque"""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.model_type = model_data['model_type']
        self.is_trained = model_data['is_trained']
        self.model_version = model_data['model_version']
        self.feature_extractor = model_data['feature_extractor']
        
        logger.info(f"Modèle chargé depuis {path}")


class MatchWinnerPredictor(BaseModel):
    """
    Prédicteur du vainqueur d'un match (1X2)
    Utilise Random Forest pour la classification
    """
    
    def __init__(self):
        super().__init__("match_winner")
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.classes = ['team1', 'team2', 'draw']
    
    def train(self, events: List[Event], outcomes: List[str]) -> None:
        """Entraîne le modèle sur des données historiques"""
        if len(events) != len(outcomes):
            raise ValueError("Le nombre d'événements doit correspondre au nombre de résultats")
        
        # Extraire les features
        features_list = []
        for event in events:
            features = self.feature_extractor.extract_all_features(event)
            features_list.append(features)
        
        # Créer le DataFrame
        df = pd.DataFrame(features_list)
        
        # Encoder les outcomes
        y = [self.classes.index(outcome) if outcome in self.classes else 0 for outcome in outcomes]
        
        # Diviser en train/test
        X_train, X_test, y_train, y_test = train_test_split(
            df, y, test_size=0.2, random_state=42
        )
        
        # Entraîner le modèle
        self.model.fit(X_train, y_train)
        
        # Évaluer
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"Accuracy du modèle MatchWinner: {accuracy:.2%}")
        
        self.is_trained = True
    
    def predict(self, event: Event) -> Prediction:
        """Prédit le vainqueur d'un match"""
        if not self.is_trained:
            logger.warning("Modèle non entraîné, utilisation de prédiction basée sur les cotes")
            return self._predict_from_odds(event)
        
        # Extraire les features
        features = self.feature_extractor.extract_all_features(event)
        df = pd.DataFrame([features])
        
        # Prédire
        prediction_idx = self.model.predict(df)[0]
        probabilities = self.model.predict_proba(df)[0]
        
        prediction = self.classes[prediction_idx]
        confidence = max(probabilities)
        
        prob_distribution = {
            self.classes[i]: prob 
            for i, prob in enumerate(probabilities)
        }
        
        return Prediction(
            event_id=event.event_id,
            prediction_type=PredictionType.MATCH_WINNER,
            predicted_value=prediction,
            confidence=confidence,
            probability_distribution=prob_distribution,
            features_used=list(features.keys()),
            model_version=self.model_version
        )
    
    def _predict_from_odds(self, event: Event) -> Prediction:
        """Prédiction basée uniquement sur les cotes (fallback)"""
        features = self.feature_extractor.extract_odds_features(event)
        
        team1_prob = features.get('team1_implied_prob', 0.5)
        team2_prob = features.get('team2_implied_prob', 0.5)
        draw_prob = 1.0 - team1_prob - team2_prob
        
        # Ajuster pour les matchs en cours
        if event.score and event.score.time_seconds > 0:
            # En live, donner plus de poids au score actuel
            if event.score.team1_score > event.score.team2_score:
                team1_prob *= 1.2
                team2_prob *= 0.8
            elif event.score.team2_score > event.score.team1_score:
                team2_prob *= 1.2
                team1_prob *= 0.8
            
            # Normaliser
            total = team1_prob + team2_prob + draw_prob
            team1_prob /= total
            team2_prob /= total
            draw_prob /= total
        
        # Déterminer la prédiction
        probs = {
            'team1': team1_prob,
            'team2': team2_prob,
            'draw': draw_prob
        }
        
        prediction = max(probs.keys(), key=probs.get)
        confidence = probs[prediction]
        
        return Prediction(
            event_id=event.event_id,
            prediction_type=PredictionType.MATCH_WINNER,
            predicted_value=prediction,
            confidence=confidence,
            probability_distribution=probs,
            features_used=['odds_based'],
            model_version="odds_fallback"
        )


class OverUnderPredictor(BaseModel):
    """
    Prédicteur Over/Under
    Prédit si le score total sera au-dessus ou en-dessous d'un seuil
    """
    
    def __init__(self):
        super().__init__("over_under")
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self.thresholds = [2.5, 3.5, 4.5, 5.5, 6.5]
    
    def predict(self, event: Event, threshold: float = 2.5) -> Prediction:
        """Prédit Over/Under pour un seuil donné"""
        # Extraire les features
        features = self.feature_extractor.extract_all_features(event)
        
        # Ajouter le seuil comme feature
        features['threshold'] = threshold
        
        # Prédiction basée sur les cotes Over/Under disponibles
        over_odds = None
        under_odds = None
        
        for odds in event.odds + event.additional_odds:
            if odds.bet_type == 9 and odds.parameter == threshold:
                over_odds = odds.coefficient
            elif odds.bet_type == 10 and odds.parameter == threshold:
                under_odds = odds.coefficient
        
        if over_odds and under_odds:
            # Calculer les probabilités implicites
            over_prob = (1/over_odds) / (1/over_odds + 1/under_odds)
            under_prob = (1/under_odds) / (1/over_odds + 1/under_odds)
            
            # Ajuster selon le score actuel en live
            if event.score and event.is_live:
                current_total = event.score.team1_score + event.score.team2_score
                remaining_time = 300 - event.score.time_seconds  # Supposons 5min match
                
                # Si score déjà proche du seuil, ajuster
                if current_total >= threshold - 1:
                    over_prob *= 1.3
                    under_prob *= 0.7
                elif current_total <= threshold - 2:
                    under_prob *= 1.2
                    over_prob *= 0.8
                
                # Normaliser
                total = over_prob + under_prob
                over_prob /= total
                under_prob /= total
            
            prediction = 'over' if over_prob > under_prob else 'under'
            confidence = max(over_prob, under_prob)
            
            prob_distribution = {'over': over_prob, 'under': under_prob}
            
            return Prediction(
                event_id=event.event_id,
                prediction_type=PredictionType.OVER_UNDER,
                predicted_value=prediction,
                confidence=confidence,
                probability_distribution=prob_distribution,
                features_used=list(features.keys()) + ['odds_analysis'],
                model_version="odds_based"
            )
        
        # Fallback: prédiction basique
        logger.warning(f"Pas de cotes Over/Under disponibles pour seuil {threshold}")
        
        # Utiliser le score actuel comme indicateur
        if event.score and event.is_live:
            current_total = event.score.team1_score + event.score.team2_score
            prediction = 'over' if current_total >= threshold else 'under'
            confidence = 0.6  # Confiance modérée
        else:
            # Prédiction par défaut basée sur les cotes moyennes
            prediction = 'over'
            confidence = 0.5
        
        return Prediction(
            event_id=event.event_id,
            prediction_type=PredictionType.OVER_UNDER,
            predicted_value=prediction,
            confidence=confidence,
            probability_distribution={'over': 0.5, 'under': 0.5},
            features_used=['fallback'],
            model_version="fallback"
        )


class PredictionEngine:
    """
    Moteur de prédiction principal
    Coordonne tous les modèles de prédiction
    """
    
    def __init__(self):
        self.match_winner_predictor = MatchWinnerPredictor()
        self.over_under_predictor = OverUnderPredictor()
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        logger.info("Moteur de prédiction initialisé")
    
    def predict_match(self, event: Event) -> Prediction:
        """Prédit le vainqueur d'un match"""
        return self.match_winner_predictor.predict(event)
    
    def predict_over_under(self, event: Event, threshold: float = 2.5) -> Prediction:
        """Prédit Over/Under"""
        return self.over_under_predictor.predict(event, threshold)
    
    def predict_all(self, event: Event) -> Dict[str, Prediction]:
        """Génère toutes les prédictions pour un événement"""
        predictions = {}
        
        # PRIORITÉ 1: Prédicteur basé sur CSV historique
        try:
            from .csv_predictor import get_csv_predictor
            csv_pred = get_csv_predictor()
            
            stats = csv_pred.get_statistics()
            if stats['csv_loaded'] and stats['total_matches_analyzed'] > 0:
                logger.info(f"✅ Utilisation du prédicteur CSV ({stats['total_matches_analyzed']} matchs analysés)")
                csv_predictions = csv_pred.predict_all(
                    event.team1_name,
                    event.team2_name,
                    event.league_name
                )
                
                # Convertir les prédictions CSV en objets Prediction
                for pred_type, pred_data in csv_predictions.items():
                    predictions[pred_type] = Prediction(
                        event_id=event.event_id,
                        prediction_type=PredictionType.MATCH_WINNER if pred_type == 'match_winner' else PredictionType.OVER_UNDER,
                        predicted_value=pred_data['predicted_value'],
                        confidence=pred_data['confidence'],
                        probability_distribution=pred_data['probability_distribution'],
                        features_used=['csv_4369_matches', 'team_names', 'league'],
                        model_version=pred_data['model_version']
                    )
                
                # Si nous avons des prédictions CSV, les utiliser
                if predictions:
                    logger.info(f"✅ Prédictions CSV générées: {list(predictions.keys())}")
                    return predictions
        except Exception as e:
            logger.warning(f"⚠️ Prédicteur CSV non disponible: {e}")
        
        # PRIORITÉ 2: Fallback vers les modèles de base
        logger.info("Utilisation des modèles de base (fallback)")
        predictions['match_winner'] = self.predict_match(event)
        predictions['over_under_2.5'] = self.predict_over_under(event, 2.5)
        predictions['over_under_3.5'] = self.predict_over_under(event, 3.5)
        predictions['over_under_4.5'] = self.predict_over_under(event, 4.5)
        
        return predictions
    
    def train_models(self, events: List[Event], outcomes: Dict[str, List[Any]]) -> None:
        """Entraîne tous les modèles avec des données historiques"""
        logger.info("Début de l'entraînement des modèles...")
        
        if 'match_winner' in outcomes:
            self.match_winner_predictor.train(events, outcomes['match_winner'])
            self.match_winner_predictor.save_model(
                self.models_dir / "match_winner_model.pkl"
            )
        
        logger.info("Entraînement des modèles terminé")
    
    def load_models(self) -> None:
        """Charge tous les modèles entraînés"""
        match_winner_path = self.models_dir / "match_winner_model.pkl"
        
        if match_winner_path.exists():
            self.match_winner_predictor.load_model(str(match_winner_path))
            logger.info("Modèles chargés avec succès")
        else:
            logger.warning("Aucun modèle entraîné trouvé, utilisation des fallbacks")


# Instance globale du moteur de prédiction
prediction_engine = PredictionEngine()


def get_prediction_engine() -> PredictionEngine:
    """Retourne l'instance singleton du moteur de prédiction"""
    return prediction_engine
