"""
ONE-DELUX-FAST - Plateforme FastAPI conforme au manifeste 1.1.0
SOLITAIRE HACK - Architecture professionnelle

Service dédié à l'intégration externe:
- découverte JSON sur /
- santé sur /health
- manifeste machine-readable sur /platform_integration.json
- API de modèles et de prédiction sous /api/*
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from one_delux_fast.platform_predictor import get_platform_prediction_service


logger = logging.getLogger(__name__)


class PredictionRequest(BaseModel):
    league: str = Field(..., min_length=1)
    homeTeam: str = Field(..., min_length=1)
    awayTeam: str = Field(..., min_length=1)
    home_odds: float
    draw_odds: float
    away_odds: float
    match_datetime: Optional[str] = None
    home_form_rate: Optional[float] = None
    away_form_rate: Optional[float] = None
    home_attack_avg: Optional[float] = None
    away_attack_avg: Optional[float] = None
    home_defense_avg: Optional[float] = None
    away_defense_avg: Optional[float] = None
    head_to_head_matches: Optional[int] = None
    head_to_head_home_winrate: Optional[float] = None


service = get_platform_prediction_service()
project_root = Path(__file__).resolve().parent
manifest_path = project_root / "platform_integration.json"

app = FastAPI(
    title="ONE DELUX AI 3.0",
    version="3.0.0",
    description="Platform integration API for prediction and model discovery",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    errors = {str(index): error.get("msg", "field required") for index, error in enumerate(exc.errors())}
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": errors,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(_, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    logger.exception("Unhandled platform API error")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/")
async def root():
    return service.get_root_payload()


@app.get("/health")
async def health():
    return service.get_health_payload()


@app.get("/platform_integration.json")
async def integration_manifest():
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Not Found")
    with manifest_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@app.get("/api/status")
async def api_status():
    return service.get_status()


@app.get("/api/models")
async def api_models():
    return {
        "models_loaded": service.get_status().get("models_loaded", 0),
        "models": service.list_models(),
    }


@app.post("/api/predict")
async def api_predict(payload: PredictionRequest):
    return service.predict(payload.model_dump())


@app.post("/api/predict/fusion")
async def api_predict_fusion(payload: PredictionRequest):
    return service.predict(payload.model_dump())


@app.post("/api/predict/over-under")
async def api_predict_over_under(payload: PredictionRequest):
    return service.predict_over_under(payload.model_dump())


@app.post("/api/predict/home-goals")
async def api_predict_home_goals(payload: PredictionRequest):
    return service.predict_home_goals(payload.model_dump())


@app.post("/api/predict/away-goals")
async def api_predict_away_goals(payload: PredictionRequest):
    return service.predict_away_goals(payload.model_dump())


@app.post("/api/predict/total-goals")
async def api_predict_total_goals(payload: PredictionRequest):
    return service.predict_total_goals(payload.model_dump())


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    import uvicorn

    uvicorn.run("platform_service:app", host=host, port=port, reload=reload, log_level="info")


if __name__ == "__main__":
    start_server(host="0.0.0.0", port=8000, reload=True)
