"""
ONE-DELUX-FAST - Plateforme de prédiction via API externe exclusive
SOLITAIRE HACK - Architecture professionnelle

Cette couche utilise UNIQUEMENT l'API externe pour les prédictions.
Aucune logique locale de prédiction n'est utilisée.
Toutes les prédictions proviennent de: https://ai-p-hcuo.onrender.com
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

import requests  # type: ignore

def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    if value is None:
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _format_score(home_goals: int, away_goals: int) -> str:
    return f"{home_goals}-{away_goals}"


class PlatformPredictionService:
    """
    Service qui utilise UNIQUEMENT l'API externe pour les prédictions.

    Les données d'entrée suivent le schéma documenté dans
    `platform_integration.json`.
    """

    def __init__(self, manifest_path: Optional[Path] = None):
        self.project_root = Path(__file__).resolve().parent.parent
        self.manifest_path = manifest_path or self.project_root / "platform_integration.json"
        self.manifest = self._load_manifest()
        self.api_base_url = self.manifest.get("base_url", "https://ai-p-hcuo.onrender.com")

    def _load_manifest(self) -> Dict[str, Any]:
        if not self.manifest_path.exists():
            logger.warning("Manifest d'intégration introuvable: %s", self.manifest_path)
            return {}

        try:
            with self.manifest_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception as exc:
            logger.error("Impossible de lire le manifeste d'intégration: %s", exc)
            return {}

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.manifest.get("name", "AI-P Platform Integration Manifest"),
            "version": self.manifest.get("version", "1.1.0"),
            "base_url": self.api_base_url,
            "status": "ok",
            "source": "ONE DELUX AI 2.0 - External API",
            "prediction_source": "external_api"
        }

    def list_models(self) -> List[Dict[str, Any]]:
        return []

    def get_root_payload(self) -> Dict[str, Any]:
        status = self.get_status()
        return {
            "status": "ok",
            "name": "ONE DELUX AI 3.0",
            "version": "3.0.0",
            "docs": "/docs",
            "openapi": "/openapi.json",
            "health": "/api/status",
            "models": "/api/models",
            "predict": "/api/predict",
            "integration_manifest": "/platform_integration.json",
            "prediction_source": "external_api",
            "external_api_url": self.api_base_url
        }

    def get_health_payload(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "prediction_source": "external_api",
            "external_api_url": self.api_base_url
        }

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize payload to camelCase and filter out None values for external API"""
        normalized = {}
        
        # Handle both snake_case and camelCase for team names
        home_team = payload.get("home_team") or payload.get("homeTeam", "")
        away_team = payload.get("away_team") or payload.get("awayTeam", "")
        
        # Always use camelCase for external API
        normalized["homeTeam"] = str(home_team).strip()
        normalized["awayTeam"] = str(away_team).strip()
        normalized["league"] = str(payload.get("league", "")).strip()
        normalized["home_odds"] = payload.get("home_odds")
        normalized["draw_odds"] = payload.get("draw_odds")
        normalized["away_odds"] = payload.get("away_odds")
        
        # Only include optional fields if they have values
        optional_fields = [
            "match_datetime", "home_form_rate", "away_form_rate",
            "home_attack_avg", "away_attack_avg", "home_defense_avg",
            "away_defense_avg", "head_to_head_matches", "head_to_head_home_winrate"
        ]
        
        for field in optional_fields:
            value = payload.get(field)
            if value is not None:
                normalized[field] = value
        
        return normalized

    def validate_payload(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        errors: List[Dict[str, Any]] = []
        required_fields_camel = ("league", "homeTeam", "awayTeam", "home_odds", "draw_odds", "away_odds")
        required_fields_snake = ("league", "home_team", "away_team", "home_odds", "draw_odds", "away_odds")
        
        # Check if payload uses snake_case or camelCase
        uses_snake = any(key in payload for key in ["home_team", "away_team"])
        required_fields = required_fields_snake if uses_snake else required_fields_camel
        
        for field in required_fields:
            value = payload.get(field)
            if value is None or value == "":
                errors.append({"loc": [field], "msg": "field required", "type": "missing"})
        return errors

    def _call_external_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call external API for predictions"""
        try:
            # Normalize payload to camelCase for external API
            normalized = self._normalize_payload(payload)
            
            # Call external API
            response = requests.post(
                f"{self.api_base_url}/api/predict",
                json=normalized,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"External API error: {response.status_code} - {response.text}")
                return {
                    "error": f"External API returned status {response.status_code}",
                    "details": response.text
                }
        except requests.exceptions.Timeout:
            logger.error("External API timeout")
            return {
                "error": "External API timeout",
                "details": "Request timed out after 10 seconds"
            }
        except requests.exceptions.ConnectionError:
            logger.error("External API connection error")
            return {
                "error": "External API connection error",
                "details": "Could not connect to external API"
            }
        except Exception as exc:
            logger.error(f"External API call failed: {exc}")
            return {
                "error": "External API call failed",
                "details": str(exc)
            }

    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get prediction from external API only"""
        # Validate payload
        errors = self.validate_payload(payload)
        if errors:
            return {
                "error": "Validation failed",
                "details": errors
            }
        
        # Call external API
        prediction = self._call_external_api(payload)
        
        # If external API returns an error, propagate it
        if "error" in prediction:
            return prediction
        
        # Return the prediction from external API
        return prediction

    def predict_over_under(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get over/under prediction from external API"""
        prediction = self.predict(payload)
        if "error" in prediction:
            return prediction
        return {
            "over_under_2_5": prediction.get("over_under_2_5"),
            "confidence": prediction.get("confidence"),
            "source": prediction.get("source", "ONE DELUX AI 2.0 - External API"),
        }

    def predict_home_goals(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get home goals prediction from external API"""
        prediction = self.predict(payload)
        if "error" in prediction:
            return prediction
        return {
            "home_goals": prediction.get("home_goals"),
            "source": prediction.get("source", "ONE DELUX AI 2.0 - External API"),
        }

    def predict_away_goals(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get away goals prediction from external API"""
        prediction = self.predict(payload)
        if "error" in prediction:
            return prediction
        return {
            "away_goals": prediction.get("away_goals"),
            "source": prediction.get("source", "ONE DELUX AI 2.0 - External API"),
        }

    def predict_total_goals(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get total goals prediction from external API"""
        prediction = self.predict(payload)
        if "error" in prediction:
            return prediction
        return {
            "total_goals": prediction.get("total_goals"),
            "source": prediction.get("source", "ONE DELUX AI 2.0 - External API"),
        }


_platform_prediction_service = PlatformPredictionService()


def get_platform_prediction_service() -> PlatformPredictionService:
    return _platform_prediction_service
