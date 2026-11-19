"""Nutrify API: upload a photo, get the dish, confidence and a calorie range.

Run from the repo root:
    uvicorn app.backend.main:app --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import config, feedback, ood
from .model_service import ImageError, ModelService, load_image

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
    state["gates"] = ood.load_gates()
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
    gates = state.get("gates")
    return {
        "status": "ok" if service else "loading",
        "classes": len(service.classes) if service else 0,
        "threshold": gates.min_confidence if gates else config.DEFAULT_THRESHOLD,
        "similarity_gate": bool(gates and gates.min_similarity is not None and service.centroids is not None),
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
        top, similarity = state["service"].predict(data)
    except ImageError as exc:
        raise HTTPException(400, str(exc))

    gates = state["gates"]
    reason = ood.check(top[0][1], similarity, gates)
    in_scope = reason is None
    calories = calories_for(top[0][0], portion) if in_scope else None
    top_out = []
    for dish, prob in top:
        name = (calories or {}).get("display_name") if dish == top[0][0] else None
        top_out.append(
            {"dish": dish, "display_name": name or pretty(dish), "confidence": round(prob, 4)}
        )
    return {
        "top": top_out,
        "confident": in_scope,  # kept for older clients: same as in_scope
        "in_scope": in_scope,
        "reason": reason,  # None, "low_confidence" or "far_from_dishes"
        "threshold": gates.min_confidence,
        "similarity": None if similarity is None else round(similarity, 4),
        "calories": calories,
    }


@app.get("/calories")
def calories(dish: str, portion: float = 1.0):
    """Calorie range for a chosen dish, without running the model (used after a correction)."""
    if dish not in state["service"].classes:
        raise HTTPException(404, "Unknown dish")
    if not config.PORTION_MIN <= portion <= config.PORTION_MAX:
        raise HTTPException(
            422, f"portion must be between {config.PORTION_MIN} and {config.PORTION_MAX}"
        )
    info = calories_for(dish, portion)
    if info is None:
        raise HTTPException(503, "Calorie data is not available")
    return info


@app.post("/feedback")
async def submit_feedback(file: UploadFile = File(...), corrected_label: str = Form(...)):
    """Record what the dish really is. corrected_label is one of the 14 dishes or "none"."""
    classes = state["service"].classes
    if corrected_label != "none" and corrected_label not in classes:
        raise HTTPException(422, "corrected_label must be one of the 14 dishes or 'none'")
    data = await file.read(config.MAX_UPLOAD_BYTES + 1)
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Image is larger than 10 MB")
    try:
        image = load_image(data)
        # Re-run the model here so the stored prediction cannot be edited by the client.
        top, similarity = state["service"].predict(data)
    except ImageError as exc:
        raise HTTPException(400, str(exc))

    reason = ood.check(top[0][1], similarity, state["gates"])
    in_scope = reason is None
    record = feedback.save_feedback(image, data, {
        "predicted_label": top[0][0],
        "confidence": round(top[0][1], 4),
        "in_scope": in_scope,
        "reason": reason,
        "similarity": None if similarity is None else round(similarity, 4),
        "top3": [{"dish": d, "confidence": round(p, 4)} for d, p in top],
        "corrected_label": corrected_label,
        "was_correct": in_scope and corrected_label == top[0][0],
    })
    return {"saved": True, "id": record["id"], "was_correct": record["was_correct"]}
