"""Tests for /calories and /feedback. They need checkpoints/efficientnet_best.pt."""
import io
import json

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.backend import config
from app.backend.main import app

pytestmark = pytest.mark.skipif(
    not config.CHECKPOINT_PATH.exists(), reason="checkpoints/efficientnet_best.pt missing"
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def feedback_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "FEEDBACK_DIR", tmp_path / "feedback")
    return tmp_path / "feedback"


def jpeg_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (200, 150), (180, 90, 30)).save(buf, format="JPEG")
    return buf.getvalue()


def post(client, label):
    return client.post(
        "/feedback",
        files={"file": ("x.jpg", jpeg_bytes(), "image/jpeg")},
        data={"corrected_label": label},
    )


def test_calories_scales_with_portion(client):
    one = client.get("/calories", params={"dish": "nihari", "portion": 1}).json()
    two = client.get("/calories", params={"dish": "nihari", "portion": 2}).json()
    assert abs(two["kcal_typical"] - 2 * one["kcal_typical"]) <= 1


def test_calories_rejects_unknown_dish_and_bad_portion(client):
    assert client.get("/calories", params={"dish": "pizza"}).status_code == 404
    assert client.get("/calories", params={"dish": "nihari", "portion": 99}).status_code == 422


def test_feedback_is_stored(client, feedback_dir):
    r = post(client, "samosa")
    assert r.status_code == 200 and r.json()["saved"] is True
    lines = (feedback_dir / "corrections.jsonl").read_text().strip().splitlines()
    rec = json.loads(lines[0])
    assert rec["corrected_label"] == "samosa"
    assert len(rec["top3"]) == 3
    assert (feedback_dir / rec["image"]).exists()
    assert rec["image_sha256"] and rec["timestamp"]


def test_feedback_none_label_is_allowed(client, feedback_dir):
    assert post(client, "none").status_code == 200


def test_feedback_rejects_bad_label_and_bad_file(client, feedback_dir):
    assert post(client, "pizza").status_code == 422
    r = client.post("/feedback", files={"file": ("x.txt", b"hi", "text/plain")}, data={"corrected_label": "samosa"})
    assert r.status_code == 400
    assert not (feedback_dir / "corrections.jsonl").exists()
