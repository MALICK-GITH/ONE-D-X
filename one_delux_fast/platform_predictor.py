"""
ONE-DELUX-FAST - Plateforme de prédiction via manifeste d'intégration
SOLITAIRE HACK - Architecture professionnelle

Cette couche traduit le contrat de `platform_integration.json` en
prédictions exploitables localement. Les modèles `.joblib` sont chargés
si présents, sinon le service bascule sur des heuristiques déterministes.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import joblib  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    joblib = None


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


@dataclass
class PlatformModelSlot:
    name: str
    filename: str
    description: str
    loaded: bool = False
    source: str = "fallback"
    artifact_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PlatformPredictionService:
    """
    Service local qui implémente le contrat du manifeste d'intégration.

    Les données d'entrée suivent le schéma documenté dans
    `platform_integration.json`.
    """

    def __init__(self, manifest_path: Optional[Path] = None):
        self.project_root = Path(__file__).resolve().parent.parent
        self.manifest_path = manifest_path or self.project_root / "platform_integration.json"
        self.models_dir = self.project_root / "models"
        self.manifest = self._load_manifest()
        self.model_slots = self._build_model_slots()
        self._load_artifacts()

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

    def _build_model_slots(self) -> Dict[str, PlatformModelSlot]:
        contract = self.manifest.get("model_contract", {})
        filenames = contract.get("model_files", [])
        descriptions = {
            "over_under_2.5.joblib": "Modèle de dépassement 2.5 buts",
            "team_home_goals.joblib": "Modèle de buts équipe domicile",
            "team_away_goals.joblib": "Modèle de buts équipe extérieur",
            "match_total_goals.joblib": "Modèle de buts totaux du match",
        }

        slots: Dict[str, PlatformModelSlot] = {}
        for filename in filenames:
            key = Path(filename).stem
            slots[key] = PlatformModelSlot(
                name=key,
                filename=filename,
                description=descriptions.get(filename, key.replace("_", " ").title()),
            )
        return slots

    def _load_artifacts(self) -> None:
        for slot in self.model_slots.values():
            artifact_path = self.models_dir / slot.filename
            slot.artifact_path = str(artifact_path)

            if not artifact_path.exists():
                logger.info("Artefact absent, fallback actif pour %s", slot.name)
                continue

            if joblib is None:
                logger.warning("joblib indisponible, fallback actif pour %s", slot.name)
                continue

            try:
                joblib.load(artifact_path)
                slot.loaded = True
                slot.source = "joblib"
                logger.info("Modèle chargé: %s", artifact_path.name)
            except Exception as exc:
                logger.warning("Chargement impossible pour %s: %s", artifact_path.name, exc)

    def _manifest_base(self) -> Dict[str, Any]:
        return {
            "name": self.manifest.get("name", "AI-P Platform Integration Manifest"),
            "version": self.manifest.get("version", "1.0.0"),
            "base_url": self.manifest.get("base_url", ""),
            "auth": self.manifest.get("auth", {"type": "none"}),
            "content_type": self.manifest.get("content_type", "application/json"),
        }

    def get_status(self) -> Dict[str, Any]:
        loaded_artifacts = sum(1 for slot in self.model_slots.values() if slot.loaded)
        model_contract = self.manifest.get("model_contract", {})
        return {
            **self._manifest_base(),
            "status": "ok",
            "models_loaded": model_contract.get("models_loaded", len(self.model_slots)),
            "loaded_artifacts": loaded_artifacts,
            "fallback_mode": loaded_artifacts < len(self.model_slots),
            "source": "ONE DELUX AI 2.0",
        }

    def list_models(self) -> List[Dict[str, Any]]:
        return [slot.to_dict() for slot in self.model_slots.values()]

    def _extract_market_probs(
        self,
        home_odds: Optional[float],
        draw_odds: Optional[float],
        away_odds: Optional[float],
    ) -> Dict[str, float]:
        odds = [value for value in (home_odds, draw_odds, away_odds) if value and value > 0]
        if not odds:
            return {"home": 0.5, "draw": 0.0, "away": 0.5}

        raw_home = 1.0 / home_odds if home_odds and home_odds > 0 else 0.0
        raw_draw = 1.0 / draw_odds if draw_odds and draw_odds > 0 else 0.0
        raw_away = 1.0 / away_odds if away_odds and away_odds > 0 else 0.0
        total = raw_home + raw_draw + raw_away

        if total <= 0:
            return {"home": 0.5, "draw": 0.0, "away": 0.5}

        return {
            "home": raw_home / total,
            "draw": raw_draw / total,
            "away": raw_away / total,
        }

    def _completeness_score(self, payload: Dict[str, Any]) -> float:
        optional_keys = [
            "home_form_rate",
            "away_form_rate",
            "home_attack_avg",
            "away_attack_avg",
            "home_defense_avg",
            "away_defense_avg",
            "head_to_head_matches",
            "head_to_head_home_winrate",
        ]
        present = sum(1 for key in optional_keys if payload.get(key) is not None)
        return present / len(optional_keys)

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(payload)
        normalized["homeTeam"] = str(payload.get("homeTeam", "")).strip()
        normalized["awayTeam"] = str(payload.get("awayTeam", "")).strip()
        normalized["league"] = str(payload.get("league", "")).strip()
        normalized["home_odds"] = _safe_float(payload.get("home_odds"))
        normalized["draw_odds"] = _safe_float(payload.get("draw_odds"))
        normalized["away_odds"] = _safe_float(payload.get("away_odds"))
        normalized["home_form_rate"] = _safe_float(payload.get("home_form_rate"), 0.5)
        normalized["away_form_rate"] = _safe_float(payload.get("away_form_rate"), 0.5)
        normalized["home_attack_avg"] = _safe_float(payload.get("home_attack_avg"), 1.5)
        normalized["away_attack_avg"] = _safe_float(payload.get("away_attack_avg"), 1.5)
        normalized["home_defense_avg"] = _safe_float(payload.get("home_defense_avg"), 1.2)
        normalized["away_defense_avg"] = _safe_float(payload.get("away_defense_avg"), 1.2)
        normalized["head_to_head_matches"] = _safe_int(payload.get("head_to_head_matches"), 0)
        normalized["head_to_head_home_winrate"] = _safe_float(payload.get("head_to_head_home_winrate"), 0.5)
        normalized["match_datetime"] = payload.get("match_datetime")
        return normalized

    def _predict_goals(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = self._normalize_payload(payload)
        probs = self._extract_market_probs(
            data["home_odds"], data["draw_odds"], data["away_odds"]
        )

        home_form = data["home_form_rate"] or 0.5
        away_form = data["away_form_rate"] or 0.5
        home_attack = data["home_attack_avg"] or 1.5
        away_attack = data["away_attack_avg"] or 1.5
        home_defense = data["home_defense_avg"] or 1.2
        away_defense = data["away_defense_avg"] or 1.2
        h2h_matches = data["head_to_head_matches"] or 0
        h2h_home_winrate = data["head_to_head_home_winrate"] or 0.5

        draw_pressure = 0.5 - probs["draw"]
        attack_pressure = ((home_attack + away_attack) - 3.0) * 0.35
        form_pressure = ((home_form + away_form) - 1.0) * 0.45
        defense_pressure = ((2.0 - home_defense) + (2.0 - away_defense)) * 0.22
        h2h_pressure = 0.0
        if h2h_matches >= 3:
            h2h_pressure = (h2h_home_winrate - 0.5) * 0.35

        expected_total = 2.35 + draw_pressure * 1.05 + attack_pressure + form_pressure + defense_pressure + h2h_pressure
        expected_total = _clamp(expected_total, 0.5, 6.5)

        home_share = (
            0.55 * probs["home"]
            + 0.18 * home_form
            + 0.16 * (home_attack / 3.0)
            + 0.06 * (2.0 - away_defense) / 2.0
            + 0.05 * h2h_home_winrate
        )
        away_share = (
            0.55 * probs["away"]
            + 0.18 * away_form
            + 0.16 * (away_attack / 3.0)
            + 0.06 * (2.0 - home_defense) / 2.0
            + 0.05 * (1.0 - h2h_home_winrate)
        )
        total_share = home_share + away_share
        if total_share <= 0:
            home_share = away_share = 0.5
            total_share = 1.0

        home_expected = expected_total * (home_share / total_share)
        away_expected = expected_total * (away_share / total_share)

        home_goals = int(_clamp(round(home_expected), 0, 6))
        away_goals = int(_clamp(round(away_expected), 0, 6))
        total_goals = home_goals + away_goals
        over_under = "OVER" if expected_total >= 2.5 else "UNDER"

        confidence = 58.0
        confidence += abs(probs["home"] - probs["away"]) * 18.0
        confidence += abs(home_form - away_form) * 10.0
        confidence += abs(home_attack - away_attack) * 3.5
        confidence += self._completeness_score(data) * 12.0
        confidence += min(8.0, abs(expected_total - total_goals) * 3.0)
        confidence = _clamp(confidence, 50.0, 96.0)

        return {
            "home_goals": home_goals,
            "away_goals": away_goals,
            "total_goals": total_goals,
            "over_under_2_5": over_under,
            "score_prediction": _format_score(home_goals, away_goals),
            "confidence": round(confidence, 1),
            "source": "ONE DELUX AI 2.0",
            "models_used": [slot.name for slot in self.model_slots.values()],
            "market_probabilities": {
                "home": round(probs["home"], 4),
                "draw": round(probs["draw"], 4),
                "away": round(probs["away"], 4),
            },
        }

    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._predict_goals(payload)

    def predict_over_under(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prediction = self._predict_goals(payload)
        return {
            "over_under_2_5": prediction["over_under_2_5"],
            "confidence": prediction["confidence"],
            "source": prediction["source"],
        }

    def predict_home_goals(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prediction = self._predict_goals(payload)
        return {
            "home_goals": prediction["home_goals"],
            "source": prediction["source"],
        }

    def predict_away_goals(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prediction = self._predict_goals(payload)
        return {
            "away_goals": prediction["away_goals"],
            "source": prediction["source"],
        }

    def predict_total_goals(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prediction = self._predict_goals(payload)
        return {
            "total_goals": prediction["total_goals"],
            "source": prediction["source"],
        }


_platform_prediction_service = PlatformPredictionService()


def get_platform_prediction_service() -> PlatformPredictionService:
    return _platform_prediction_service
