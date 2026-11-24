import io

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.lv_outline import model as m
from app.main import app

client = TestClient(app)


def _png(h=112, w=112):
    img = np.random.default_rng(1).integers(0, 255, (h, w, 3), dtype=np.uint8)
    return cv2.imencode(".png", img)[1].tobytes()


def _upload(data: bytes, name: str):
    return client.post("/uploads", files={"file": (name, io.BytesIO(data))})


class FakeSession:
    """ONNX stand-in: positive logits inside a disc (plus an optional stray speck)."""

    def __init__(self, speck=False, empty=False):
        self.speck, self.empty = speck, empty

    def run(self, names, feed):
        assert feed["image"].shape == (1, 3, 112, 112) and feed["image"].dtype == np.float32
        logits = np.full((1, 1, 112, 112), -6.0, dtype=np.float32)
        if not self.empty:
            yy, xx = np.mgrid[:112, :112]
            logits[0, 0][(yy - 56) ** 2 + (xx - 56) ** 2 < 30 ** 2] = 4.0
            if self.speck:
                logits[0, 0, 5:9, 5:9] = 4.0
        return [logits]


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_upload_roundtrip_and_empty_rejected():
    assert _upload(b"abc", "a.png").json()["file_url"].endswith(".png")
    assert _upload(b"", "a.png").status_code == 400


def test_predict_without_weights_returns_fallback(monkeypatch):
    monkeypatch.setattr(m, "_model_available", lambda: False)
    monkeypatch.setattr(m, "_session", None)
    url = _upload(_png(), "a.png").json()["file_url"]
    r = client.post("/lv-outline/predict", json={"file_url": url})
    assert r.status_code == 200 and "weights not found" in r.json()["summary"]


def test_predict_rejects_non_image():
    url = _upload(b"this is not an image", "notes.txt").json()["file_url"]
    r = client.post("/lv-outline/predict", json={"file_url": url})
    assert r.status_code == 422 and "detail" in r.json()


def test_predict_returns_mask_overlay_contour(monkeypatch):
    monkeypatch.setattr(m, "_session", FakeSession())
    url = _upload(_png(224, 224), "a.png").json()["file_url"]
    j = client.post("/lv-outline/predict", json={"file_url": url}).json()
    expected = np.pi * 30 ** 2 / 112 ** 2
    assert abs(j["area_fraction"] - expected) < 0.02
    assert j["width"] == 448 and j["height"] == 448  # small frames are upscaled for display
    assert len(j["contour"]) >= 8 and all(0 <= x <= 1 and 0 <= y <= 1 for x, y in j["contour"])
    assert j["confidence"] > 0.95
    for k in ("original_image_base64", "overlay_image_base64", "mask_base64"):
        assert j[k]


def test_large_frames_are_downscaled_for_display(monkeypatch):
    monkeypatch.setattr(m, "_session", FakeSession())
    url = _upload(_png(800, 1600), "a.png").json()["file_url"]
    j = client.post("/lv-outline/predict", json={"file_url": url}).json()
    assert (j["width"], j["height"]) == (640, 320)


def test_stray_speck_is_dropped(monkeypatch):
    monkeypatch.setattr(m, "_session", FakeSession(speck=True))
    url = _upload(_png(), "a.png").json()["file_url"]
    j = client.post("/lv-outline/predict", json={"file_url": url}).json()
    assert abs(j["area_fraction"] - np.pi * 30 ** 2 / 112 ** 2) < 0.02  # speck (16 px) excluded


def test_no_ventricle_found(monkeypatch):
    monkeypatch.setattr(m, "_session", FakeSession(empty=True))
    url = _upload(_png(), "a.png").json()["file_url"]
    j = client.post("/lv-outline/predict", json={"file_url": url}).json()
    assert j["area_fraction"] == 0 and j["contour"] == []
    assert "No clear left ventricle" in j["summary"]
