"""Store user corrections so they can be used later to evaluate or retrain the model.

Each submission adds one JSON line to feedback/corrections.jsonl and saves the photo as
feedback/images/<id>.jpg (re-encoded, so EXIF data such as GPS location is dropped).
If the same photo is submitted again (same image_sha256), the latest line is the
user's final answer.
"""
import hashlib
import json
import threading
import uuid
from datetime import datetime, timezone

from . import config

_lock = threading.Lock()


def save_feedback(image, raw_bytes, fields):
    """Write one correction. `image` is an RGB PIL image; `fields` is a dict of labels."""
    entry_id = uuid.uuid4().hex
    folder = config.FEEDBACK_DIR
    (folder / "images").mkdir(parents=True, exist_ok=True)
    image.save(folder / "images" / f"{entry_id}.jpg", format="JPEG", quality=90)
    record = {
        "id": entry_id,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "image": f"images/{entry_id}.jpg",
        "image_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        **fields,
    }
    with _lock, open(folder / "corrections.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record
