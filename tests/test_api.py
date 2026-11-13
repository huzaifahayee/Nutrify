"""API tests. They need checkpoints/efficientnet_best.pt (not in Git)."""
import io

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
    with TestClient(app) as c:  # runs startup, which loads the model
        yield c


def jpeg_bytes(size=(300, 200), color=(180, 90, 30)):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="JPEG")
    return buf.getvalue()


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["classes"] == 14


def test_dishes(client):
    assert len(client.get("/dishes").json()) == 14


def test_predict_shape(client):
    r = client.post("/predict", files={"file": ("x.jpg", jpeg_bytes(), "image/jpeg")})
    assert r.status_code == 200
    body = r.json()
    confs = [t["confidence"] for t in body["top"]]
    assert len(confs) == 3 and confs == sorted(confs, reverse=True)
    assert 0 < sum(confs) <= 1.0001
    assert body["confident"] == (confs[0] >= body["threshold"])
    if not body["confident"]:
        assert body["calories"] is None


def test_predict_rejects_non_image(client):
    r = client.post("/predict", files={"file": ("x.txt", b"hello", "text/plain")})
    assert r.status_code == 400


def test_predict_rejects_bad_portion(client):
    r = client.post(
        "/predict",
        files={"file": ("x.jpg", jpeg_bytes(), "image/jpeg")},
        data={"portion": "100"},
    )
    assert r.status_code == 422
