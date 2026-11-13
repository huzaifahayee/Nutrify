"""Nutrify API: upload a photo, get the dish, confidence and a calorie range.

Run from the repo root:
    uvicorn app.backend.main:app --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .model_service import ImageError, ModelService

log = logging.getLogger("nutrify")

try:  # Abdullah's module; the app still works without it (calories become null)
    from src.calories import get_calories
except Exception as exc:  # ImportError, or a data file problem
    log.warning("calorie module unavailable: %s", exc)
    get_calories = None

state = {}


@asynccontextmanager
async def lifespan(app):
    state["service"] = ModelService()
    state["threshold"] = config.load_threshold()
    yield
    state.clear()


app = FastAPI(title="Nutrify API", version="1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def pretty(dish):
    return dish.replace("_", " ").title()


def calories_for(dish, portion):
    """Calorie info from src/calories.py, or None if it is not available."""
    if get_calories is None:
        return None
    try:
        info = get_calories(dish, portion)
    except Exception as exc:
        log.warning("calories failed for %s: %s", dish, exc)
        return None
    return {"portion": portion, **info}


@app.get("/health")
def health():
    service = state.get("service")
    return {
        "status": "ok" if service else "loading",
        "classes": len(service.classes) if service else 0,
        "threshold": state.get("threshold", config.DEFAULT_THRESHOLD),
        "calories_available": get_calories is not None,
    }


@app.get("/dishes")
def dishes():
    return [{"dish": d, "display_name": pretty(d)} for d in state["service"].classes]


@app.post("/predict")
async def predict(file: UploadFile = File(...), portion: float = Form(1.0)):
    if not config.PORTION_MIN <= portion <= config.PORTION_MAX:
        raise HTTPException(
            422, f"portion must be between {config.PORTION_MIN} and {config.PORTION_MAX}"
        )
    data = await file.read(config.MAX_UPLOAD_BYTES + 1)
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Image is larger than 10 MB")
    try:
        top = state["service"].predict(data)
    except ImageError as exc:
        raise HTTPException(400, str(exc))

    threshold = state["threshold"]
    confident = top[0][1] >= threshold
    calories = calories_for(top[0][0], portion) if confident else None
    top_out = []
    for dish, prob in top:
        name = (calories or {}).get("display_name") if dish == top[0][0] else None
        top_out.append(
            {"dish": dish, "display_name": name or pretty(dish), "confidence": round(prob, 4)}
        )
    return {
        "top": top_out,
        "confident": confident,
        "threshold": threshold,
        "calories": calories,
    }
