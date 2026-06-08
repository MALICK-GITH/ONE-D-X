"""
ONE-DELUX-FAST - Flask Web Application

Unified web layer for the platform:
- coherent page rendering
- normalized API payloads
- structural API analysis
- operational summaries for dashboards
"""

from collections import Counter
from datetime import datetime
import logging
import os
import re
import time
import unicodedata
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template, request

from one_delux_fast.api_client import get_api_client
from one_delux_fast.api_client import BetType
from one_delux_fast.data_manager import get_data_manager
from one_delux_fast.prediction_engine import get_prediction_engine
from one_delux_fast.platform_predictor import get_platform_prediction_service


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "one-delux-fast-dev-secret")


api_client = None
data_manager = None
prediction_engine = None
platform_prediction_service = None


def init_services() -> Dict[str, bool]:
    """Initialize optional services and expose their availability."""
    global api_client, data_manager, prediction_engine, platform_prediction_service

    status = {
        "api_client": False,
        "data_manager": False,
        "prediction_engine": False,
        "platform_prediction_service": False,
    }

    try:
        api_client = get_api_client()
        status["api_client"] = True
        logger.info("API client ready")
    except Exception as exc:
        logger.warning("API client unavailable: %s", exc)

    try:
        data_manager = get_data_manager()
        status["data_manager"] = True
        logger.info("Data manager ready")
    except Exception as exc:
        logger.warning("Data manager unavailable: %s", exc)

    try:
        prediction_engine = get_prediction_engine()
        status["prediction_engine"] = True
        logger.info("Prediction engine ready")
    except Exception as exc:
        logger.warning("Prediction engine unavailable: %s", exc)

    try:
        platform_prediction_service = get_platform_prediction_service()
        status["platform_prediction_service"] = True
        logger.info("Platform prediction service ready")
    except Exception as exc:
        logger.warning("Platform prediction service unavailable: %s", exc)

    return status


modules_status = init_services()


STATUS_META = {
    "live": {"label": "EN DIRECT", "class": "status-live", "order": 0},
    "upcoming": {"label": "À VENIR", "class": "status-upcoming", "order": 1},
    "finished": {"label": "TERMINÉ", "class": "status-finished", "order": 2},
}

FINAL_STATUS_MARKERS = (
    "termin",
    "final",
    "finished",
    "ended",
    "full time",
    "ft",
    "score final",
)
UPCOMING_STATUS_MARKERS = (
    "debut dans",
    "avant le debut",
    "avant-match",
    "paris d'avant-match",
    "paris avant le debut du jeu",
    "pre-match",
    "scheduled",
    "to start",
    "kickoff",
    "reporte",
    "postpone",
)
LIVE_STATUS_MARKERS = (
    "en cours",
    "evenement en cours",
    "event en cours",
    "live",
    "minutes",
    "minute",
    "mi-temps",
    "mi temps",
    "half",
    "periode",
)


def _normalize_text(value: Any) -> str:
    """Return a lower-case accent-free string for comparisons."""
    if value is None:
        return ""
    normalized = unicodedata.normalize("NFKD", str(value))
    stripped = "".join(char for char in normalized if not unicodedata.combining(char))
    return stripped.casefold().strip()


def _event_status_key(event: Any) -> str:
    """Infer the real match status from the score block."""
    score = getattr(event, "score", None)
    status_text = _normalize_text(getattr(score, "status", "") or "")

    if getattr(score, "is_final", False):
        return "finished"

    if status_text:
        if any(marker in status_text for marker in FINAL_STATUS_MARKERS):
            return "finished"
        if any(marker in status_text for marker in UPCOMING_STATUS_MARKERS):
            return "upcoming"
        if any(marker in status_text for marker in LIVE_STATUS_MARKERS):
            return "live"
        if status_text.startswith("<1") or re.search(r"\b\d+\s*minutes?\b", status_text):
            return "live"

    if getattr(event, "is_live", False):
        return "live"

    start_time = getattr(event, "start_time", 0) or 0
    if start_time and start_time > time.time():
        return "upcoming"

    return "upcoming"


def _event_status_details(event: Any) -> Dict[str, str]:
    key = _event_status_key(event)
    meta = STATUS_META.get(key, STATUS_META["upcoming"])
    return {
        "key": key,
        "label": meta["label"],
        "class": meta["class"],
    }


def _event_score_display(event: Any, status_key: str | None = None) -> str | None:
    if status_key is None:
        status_key = _event_status_key(event)
    if status_key == "upcoming":
        return None
    if not getattr(event, "score", None):
        return None
    return f"{event.score.team1_score}-{event.score.team2_score}"


def _serialize_event(event: Any, include_odds: bool = True) -> Dict[str, Any]:
    status = _event_status_details(event)
    score_display = _event_score_display(event, status["key"])
    start_time = datetime.fromtimestamp(event.start_time) if event.start_time else None

    def _serialize_odds(odds_list: List[Any]) -> List[Dict[str, Any]]:
        return [
            {
                "bet_type": odds.bet_type,
                "description": BetType.get_description(getattr(odds, "bet_type", 0)),
                "coefficient": odds.coefficient,
                "coefficient_str": odds.coefficient_str,
                "parameter": odds.parameter,
                "group": odds.group,
            }
            for odds in odds_list
        ]

    payload = {
        "event_id": event.event_id,
        "sport_id": event.sport_id,
        "sport_name": event.sport_name,
        "league_id": event.league_id,
        "league_name": event.league_name,
        "team1_id": event.team1_id,
        "team1_name": event.team1_name,
        "team2_id": event.team2_id,
        "team2_name": event.team2_name,
        "start_time": event.start_time,
        "start_time_iso": start_time.isoformat() if start_time else None,
        "source_is_live": event.is_live,
        "is_live": status["key"] == "live",
        "status_key": status["key"],
        "status_label": status["label"],
        "status_class": status["class"],
        "favorite_team": event.get_favorite_team(),
        "current_score": score_display,
        "score_display": score_display or ("À venir" if status["key"] == "upcoming" else "N/A"),
        "odds_count": len(event.odds),
        "additional_odds_count": len(event.additional_odds),
        "total_odds_count": len(event.odds) + len(event.additional_odds),
        "country": getattr(event, "country", None),
        "last_update": getattr(event, "last_update", None),
    }

    if include_odds:
        payload["odds"] = _serialize_odds(event.odds)
        payload["additional_odds"] = _serialize_odds(event.additional_odds)
    else:
        payload["odds"] = []
        payload["additional_odds"] = []

    return payload


def _filter_events(
    events: List[Any],
    league: str = "",
    live_only: bool = False,
    search: str = "",
    status: str = "",
) -> List[Any]:
    filtered = events
    normalized_status = (status or "").strip().lower()

    if live_only and normalized_status in {"", "all"}:
        normalized_status = "live"

    if normalized_status and normalized_status != "all":
        filtered = [event for event in filtered if _event_status_key(event) == normalized_status]
    elif live_only:
        filtered = [event for event in filtered if _event_status_key(event) == "live"]

    if league:
        filtered = [event for event in filtered if event.league_name == league]

    if search:
        needle = search.lower().strip()
        filtered = [
            event
            for event in filtered
            if needle in event.league_name.lower()
            or needle in event.sport_name.lower()
            or needle in event.team1_name.lower()
            or needle in event.team2_name.lower()
        ]

    return filtered


def _build_summary(events: List[Any]) -> Dict[str, Any]:
    leagues = Counter(event.league_name for event in events)
    sports = Counter(event.sport_name for event in events)
    statuses = Counter(_event_status_key(event) for event in events)

    return {
        "total_events": len(events),
        "live_events": statuses.get("live", 0),
        "upcoming_events": statuses.get("upcoming", 0),
        "finished_events": statuses.get("finished", 0),
        "leagues_count": len(leagues),
        "sports_count": len(sports),
        "top_leagues": [
            {"name": name, "count": count}
            for name, count in leagues.most_common(8)
        ],
        "top_sports": [
            {"name": name, "count": count}
            for name, count in sports.most_common(8)
        ],
    }


def _build_league_cards(events: List[Any]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}

    for event in events:
        status_key = _event_status_key(event)
        league_entry = grouped.setdefault(
            event.league_name,
            {
                "league_name": event.league_name,
                "league_id": event.league_id,
                "sport_name": event.sport_name,
                "total_events": 0,
                "live_events": 0,
                "upcoming_events": 0,
                "finished_events": 0,
                "matches": [],
                "sample_events": [],
            },
        )

        league_entry["total_events"] += 1
        if status_key == "live":
            league_entry["live_events"] += 1
        elif status_key == "finished":
            league_entry["finished_events"] += 1
        else:
            league_entry["upcoming_events"] += 1

        league_entry["matches"].append(_serialize_event(event, include_odds=False))
        if len(league_entry["sample_events"]) < 3:
            league_entry["sample_events"].append(_serialize_event(event, include_odds=False))

    status_order = {"live": 0, "upcoming": 1, "finished": 2}
    for league_entry in grouped.values():
        league_entry["matches"] = sorted(
            league_entry["matches"],
            key=lambda item: (
                status_order.get(item["status_key"], 9),
                item["start_time"] or 0,
                item["team1_name"],
                item["team2_name"],
            ),
        )

    return sorted(
        grouped.values(),
        key=lambda item: (-item["total_events"], item["league_name"]),
    )


def _build_api_analysis(events: List[Any]) -> Dict[str, Any]:
    return {
        "endpoint": {
            "base_url": getattr(api_client.config, "base_url", "https://888starz.bet/service-api/LiveFeed/Get1x2_VZip") if api_client else "https://888starz.bet/service-api/LiveFeed/Get1x2_VZip",
            "method": "GET",
            "top_level_keys": ["Success", "Error", "ErrorCode", "Guid", "Value"],
            "value_container": "Array of events",
        },
        "query_parameters": [
            {"name": "sports", "default": "85", "purpose": "Sport identifier"},
            {"name": "count", "default": "80", "purpose": "Number of events requested from the feed"},
            {"name": "lng", "default": "fr", "purpose": "Response language"},
            {"name": "gr", "default": "789", "purpose": "Rules / grouping"},
            {"name": "mode", "default": "4", "purpose": "Feed mode"},
            {"name": "country", "default": "96", "purpose": "Country code"},
            {"name": "partner", "default": "233", "purpose": "Partner id"},
            {"name": "getEmpty", "default": "true", "purpose": "Include empty markets"},
            {"name": "virtualSports", "default": "true", "purpose": "Include virtual sports"},
            {"name": "noFilterBlockEvent", "default": "true", "purpose": "Avoid blocked-event filtering"},
        ],
        "event_schema": [
            {"key": "I", "meaning": "Event id"},
            {"key": "N", "meaning": "Event number"},
            {"key": "T", "meaning": "Event type"},
            {"key": "SI", "meaning": "Sport id"},
            {"key": "SN", "meaning": "Sport name"},
            {"key": "LI", "meaning": "League id"},
            {"key": "L", "meaning": "League name"},
            {"key": "O1I", "meaning": "Team 1 id"},
            {"key": "O1", "meaning": "Team 1 name"},
            {"key": "O2I", "meaning": "Team 2 id"},
            {"key": "O2", "meaning": "Team 2 name"},
            {"key": "S", "meaning": "Start timestamp"},
            {"key": "ICY", "meaning": "Raw live flag from the provider"},
            {"key": "SC", "meaning": "Score block"},
            {"key": "E", "meaning": "Main odds"},
            {"key": "AE", "meaning": "Additional odds"},
            {"key": "U", "meaning": "Last update timestamp"},
            {"key": "CE", "meaning": "Country / region"},
            {"key": "CN", "meaning": "Country name"},
        ],
        "score_schema": [
            {"key": "FS.S1", "meaning": "Team 1 score"},
            {"key": "FS.S2", "meaning": "Team 2 score"},
            {"key": "TS", "meaning": "Elapsed time in seconds"},
            {"key": "SLS", "meaning": "Human-readable status"},
            {"key": "I", "meaning": "Extra status marker (e.g. final)"},
        ],
        "status_rules": [
            {
                "status_key": "live",
                "rule": "SC.SLS contains a minute counter, 'Événement en cours', or another active in-play marker",
            },
            {
                "status_key": "upcoming",
                "rule": "SC.SLS contains 'Ébut dans', 'avant le début', or a pre-match betting label",
            },
            {
                "status_key": "finished",
                "rule": "SC.SLS contains final/terminated markers or the score block is explicitly final",
            },
        ],
        "odds_schema": [
            {"key": "T", "meaning": "Bet type code"},
            {"key": "C", "meaning": "Decimal coefficient"},
            {"key": "CV", "meaning": "Coefficient as string"},
            {"key": "P", "meaning": "Parameter / threshold"},
            {"key": "G", "meaning": "Group identifier"},
        ],
        "bet_types": [
            {"code": code, "label": description}
            for code, description in [
                (1, "Team 2 outsider win"),
                (2, "Team 1 outsider win"),
                (3, "Team 1 favorite win"),
                (4, "Team 2 favorite win"),
                (5, "Double chance 1X / 12"),
                (6, "Double chance X2 / 12"),
                (7, "Team 1 positive handicap"),
                (8, "Team 1 negative handicap"),
                (9, "Over"),
                (10, "Under"),
                (11, "Team 1 scores more than"),
                (12, "Team 1 scores less than"),
                (13, "Team 2 scores more than"),
                (14, "Team 2 scores less than"),
            ]
        ],
        "live_snapshot": _build_summary(events),
        "recommendations": [
            "Cache normalized responses for short intervals",
            "Use SC.SLS instead of the provider raw live flag to derive the real match status",
            "Expose league summaries from the backend instead of regrouping on each page",
            "Keep odds and score fields versioned in one shared serializer",
            "Treat the API as volatile and guard every parsing step",
        ],
    }


def _get_current_events(force_refresh: bool = False) -> List[Any]:

    """Return the latest event list, preferably from cache."""
    if data_manager and not force_refresh:
        cached_events = data_manager.cache.get("events_current")
        if cached_events:
            return cached_events

    if not api_client:
        raise RuntimeError("API client unavailable")

    response = api_client.get_events()
    if not response.is_valid():
        raise RuntimeError(response.error or "API request failed")

    events = response.data
    if data_manager:
        data_manager.cache_events(events, ttl=30)
    return events


def _first_available_odds(event: Any, bet_types: List[int]) -> float | None:
    for bet_type in bet_types:
        odds = event.get_main_odds(bet_type)
        if odds and getattr(odds, "coefficient", None):
            return float(odds.coefficient)
    return None


def _derive_draw_odds(home_odds: float | None, away_odds: float | None) -> float:
    if home_odds and away_odds:
        return round(max(2.05, ((home_odds + away_odds) / 2.0) * 1.08), 2)
    return 3.2


def _market_probabilities_from_event(event: Any) -> Dict[str, float]:
    home_odds = _first_available_odds(event, [3, 2])
    away_odds = _first_available_odds(event, [4, 1])
    draw_odds = _derive_draw_odds(home_odds, away_odds)
    if not home_odds:
        home_odds = 2.0
    if not away_odds:
        away_odds = 2.0

    raw_home = 1.0 / home_odds
    raw_draw = 1.0 / draw_odds
    raw_away = 1.0 / away_odds
    total = raw_home + raw_draw + raw_away

    return {
        "home": raw_home / total if total else 0.5,
        "draw": raw_draw / total if total else 0.0,
        "away": raw_away / total if total else 0.5,
        "home_odds": home_odds,
        "draw_odds": draw_odds,
        "away_odds": away_odds,
    }


def _build_platform_payload_from_event(event: Any) -> Dict[str, Any]:
    market = _market_probabilities_from_event(event)
    home_prob = market["home"]
    away_prob = market["away"]
    draw_prob = market["draw"]

    return {
        "league": event.league_name,
        "homeTeam": event.team1_name,
        "awayTeam": event.team2_name,
        "home_odds": market["home_odds"],
        "draw_odds": market["draw_odds"],
        "away_odds": market["away_odds"],
        "match_datetime": datetime.fromtimestamp(event.start_time).isoformat() if event.start_time else None,
        "home_form_rate": round(min(0.95, max(0.05, home_prob + 0.1)), 3),
        "away_form_rate": round(min(0.95, max(0.05, away_prob + 0.1)), 3),
        "home_attack_avg": round(1.0 + home_prob * 1.6, 2),
        "away_attack_avg": round(1.0 + away_prob * 1.6, 2),
        "home_defense_avg": round(1.0 + away_prob * 1.0, 2),
        "away_defense_avg": round(1.0 + home_prob * 1.0, 2),
        "head_to_head_matches": 0,
        "head_to_head_home_winrate": round(min(0.95, max(0.05, home_prob + (0.5 - draw_prob) * 0.35)), 3),
    }


def _predict_platform_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not platform_prediction_service:
        raise RuntimeError("Platform prediction service unavailable")
    return platform_prediction_service.predict(payload)


@app.route("/")
def index():
    return render_template(
        "index.html",
        modules_status=modules_status,
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


@app.route("/league")
def league():
    return render_template(
        "league.html",
        league_name=request.args.get("name", "Ligue"),
        modules_status=modules_status,
    )


@app.route("/match")
def match():
    return render_template(
        "match.html",
        event_id=request.args.get("event_id", 0, type=int),
        modules_status=modules_status,
    )


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", modules_status=modules_status)


@app.route("/events")
def events():
    return render_template("events.html", modules_status=modules_status)


@app.route("/predictions")
def predictions():
    return render_template("predictions.html", modules_status=modules_status)


@app.route("/api/events")
def api_events():
    if not api_client:
        return jsonify({"success": False, "demo": True, "events": [], "summary": _build_summary([])}), 503

    try:
        events = _get_current_events()
        events = _filter_events(
            events,
            league=request.args.get("league", ""),
            live_only=request.args.get("live_only", "false").lower() == "true",
            search=request.args.get("search", ""),
            status=request.args.get("status", ""),
        )

        limit = request.args.get("limit", type=int)
        if limit is not None and limit > 0:
            events = events[:limit]

        serialized_events = [_serialize_event(event) for event in events]

        return jsonify(
            {
                "success": True,
                "events": serialized_events,
                "summary": _build_summary(events),
            }
        )
    except Exception as exc:
        logger.exception("Failed to fetch events")
        return jsonify({"success": False, "error": str(exc), "events": [], "summary": _build_summary([])}), 500


@app.route("/api/leagues")
def api_leagues():
    if not api_client:
        return jsonify({"success": False, "demo": True, "leagues": [], "summary": _build_summary([])}), 503

    try:
        events = _filter_events(
            _get_current_events(),
            search=request.args.get("search", ""),
            live_only=request.args.get("live_only", "false").lower() == "true",
            status=request.args.get("status", ""),
        )

        leagues = _build_league_cards(events)
        return jsonify({"success": True, "leagues": leagues, "summary": _build_summary(events)})
    except Exception as exc:
        logger.exception("Failed to build league summary")
        return jsonify({"success": False, "error": str(exc), "leagues": [], "summary": _build_summary([])}), 500


@app.route("/api/predictions/<int:event_id>")
def api_predictions(event_id: int):
    if not api_client or not prediction_engine:
        return jsonify({"success": False, "demo": True, "error": "Required modules unavailable"}), 503

    try:
        event = next((item for item in _get_current_events() if item.event_id == event_id), None)
        if not event:
            return jsonify({"success": False, "error": "Événement non trouvé"}), 404

        all_predictions = prediction_engine.predict_all(event)
        prediction_payload = {}
        for key, prediction in all_predictions.items():
            prediction_payload[key] = {
                "prediction_type": prediction.prediction_type.value,
                "predicted_value": prediction.predicted_value,
                "confidence": prediction.confidence,
                "confidence_percent": round(prediction.confidence * 100, 2),
                "probability_distribution": prediction.probability_distribution or {},
                "model_version": prediction.model_version,
                "features_used": prediction.features_used or [],
            }

        return jsonify(
            {
                "success": True,
                "event": _serialize_event(event),
                "predictions": prediction_payload,
                "platform": _predict_platform_payload(_build_platform_payload_from_event(event))
                if platform_prediction_service
                else None,
                "generated_at": datetime.now().isoformat(),
            }
        )
    except Exception as exc:
        logger.exception("Failed to build predictions")
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/stats")
def api_stats():
    stats: Dict[str, Any] = {
        "modules": modules_status,
        "timestamp": datetime.now().isoformat(),
    }

    if api_client:
        api_stats = api_client.get_statistics()
        stats["api"] = api_stats

    if data_manager:
        cache_stats = data_manager.cache.get_statistics()
        stats["cache"] = cache_stats

    if api_client:
        try:
            stats["summary"] = _build_summary(_get_current_events())
        except Exception as exc:
            logger.warning("Unable to enrich stats summary: %s", exc)

    if platform_prediction_service:
        stats["platform"] = platform_prediction_service.get_status()

    return jsonify(stats)


@app.route("/api/analysis")
def api_analysis():
    if not api_client:
        return jsonify({"success": False, "error": "API client unavailable", "analysis": _build_api_analysis([])}), 503

    try:
        analysis = _build_api_analysis(_get_current_events())
        return jsonify({"success": True, "analysis": analysis})
    except Exception as exc:
        logger.exception("Failed to analyze API")
        return jsonify({"success": False, "error": str(exc), "analysis": _build_api_analysis([])}), 500


@app.route("/api/status")
def api_status():
    if not platform_prediction_service:
        return jsonify({"status": "error", "error": "Platform prediction service unavailable"}), 503

    return jsonify(platform_prediction_service.get_status())


@app.route("/api/models")
def api_models():
    if not platform_prediction_service:
        return jsonify({"success": False, "error": "Platform prediction service unavailable"}), 503

    contract = platform_prediction_service.manifest.get("model_contract", {}) if platform_prediction_service.manifest else {}
    return jsonify(
        {
            "models_loaded": platform_prediction_service.get_status().get("models_loaded", 0),
            "loaded_artifacts": platform_prediction_service.get_status().get("loaded_artifacts", 0),
            "model_contract": contract,
            "models": platform_prediction_service.list_models(),
            "source": "ONE DELUX AI 2.0",
        }
    )


@app.route("/api/predict", methods=["POST"])
def api_predict():
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"success": False, "error": "JSON payload required"}), 400

    try:
        prediction = _predict_platform_payload(payload)
        return jsonify(prediction)
    except Exception as exc:
        logger.exception("Failed to generate platform prediction")
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/predict/fusion", methods=["POST"])
def api_predict_fusion():
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"success": False, "error": "JSON payload required"}), 400

    try:
        prediction = _predict_platform_payload(payload)
        return jsonify(prediction)
    except Exception as exc:
        logger.exception("Failed to generate fusion prediction")
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/predict/over-under", methods=["POST"])
def api_predict_over_under():
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"success": False, "error": "JSON payload required"}), 400

    try:
        prediction = platform_prediction_service.predict_over_under(payload) if platform_prediction_service else _predict_platform_payload(payload)
        return jsonify(prediction)
    except Exception as exc:
        logger.exception("Failed to generate over/under prediction")
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/predict/home-goals", methods=["POST"])
def api_predict_home_goals():
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"success": False, "error": "JSON payload required"}), 400

    try:
        prediction = platform_prediction_service.predict_home_goals(payload) if platform_prediction_service else _predict_platform_payload(payload)
        return jsonify(prediction)
    except Exception as exc:
        logger.exception("Failed to generate home goals prediction")
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/predict/away-goals", methods=["POST"])
def api_predict_away_goals():
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"success": False, "error": "JSON payload required"}), 400

    try:
        prediction = platform_prediction_service.predict_away_goals(payload) if platform_prediction_service else _predict_platform_payload(payload)
        return jsonify(prediction)
    except Exception as exc:
        logger.exception("Failed to generate away goals prediction")
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/predict/total-goals", methods=["POST"])
def api_predict_total_goals():
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"success": False, "error": "JSON payload required"}), 400

    try:
        prediction = platform_prediction_service.predict_total_goals(payload) if platform_prediction_service else _predict_platform_payload(payload)
        return jsonify(prediction)
    except Exception as exc:
        logger.exception("Failed to generate total goals prediction")
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    if not api_client or not data_manager:
        return jsonify({"success": False, "error": "Modules requis non disponibles"}), 503

    try:
        events = _get_current_events(force_refresh=True)
        if events:
            if data_manager:
                data_manager.cache_events(events, ttl=60)
            return jsonify(
                {
                    "success": True,
                    "message": "Données rafraîchies",
                    "summary": _build_summary(events),
                }
            )
        return jsonify({"success": False, "error": "No events returned"}), 500
    except Exception as exc:
        logger.exception("Failed to refresh data")
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/cache", methods=["DELETE"])
def api_cache():
    if not data_manager:
        return jsonify({"success": False, "error": "Data manager unavailable"}), 503

    try:
        data_manager.cache.clear()
        return jsonify({"success": True, "message": "Cache vidé avec succès"})
    except Exception as exc:
        logger.exception("Failed to clear cache")
        return jsonify({"success": False, "error": str(exc)}), 500


if __name__ == "__main__":
    logger.info("Starting ONE-DELUX-FAST Flask application")
    logger.info("Modules loaded: %s", modules_status)
    app.run(debug=True, host="0.0.0.0", port=5000)
