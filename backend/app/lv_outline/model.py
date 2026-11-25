import base64
import os

import cv2
import numpy as np

from ..common import InvalidInput, fetch_bytes

WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "weights")
MODEL_PATH = os.path.join(WEIGHTS_DIR, "lv_model.onnx")

MODEL_SIZE = 112          # network input resolution (EchoNet frames are 112x112)
MAX_DISPLAY = 640         # larger frames are scaled down to this longest side
MIN_DISPLAY = 448         # small frames (EchoNet is 112 px) are scaled up to this
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

_session = None


def _model_available() -> bool:
    return os.path.exists(MODEL_PATH)


def load_model():
    global _session
    if _session is None and _model_available():
        import onnxruntime as ort

        _session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    return _session


def _load_image(file_url: str) -> np.ndarray:
    arr = np.frombuffer(fetch_bytes(file_url), dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise InvalidInput("This endpoint needs an echocardiogram frame as an image (PNG/JPG).")
    return image


def _preprocess(image: np.ndarray) -> np.ndarray:
    small = cv2.resize(image, (MODEL_SIZE, MODEL_SIZE), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    x = (rgb.astype(np.float32) / 255.0 - MEAN) / STD
    return x.transpose(2, 0, 1)[None, ...].astype(np.float32)


def largest_component(mask: np.ndarray) -> np.ndarray:
    """Keep only the biggest connected blob; the left ventricle is a single structure."""
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    if n <= 1:
        return mask.astype(np.uint8)
    keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return (labels == keep).astype(np.uint8)


def contour_points(mask: np.ndarray) -> list:
    """Simplified outline of the mask as [[x, y], ...] normalised to 0..1."""
    cnts, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cnts:
        return []
    c = max(cnts, key=cv2.contourArea)
    c = cv2.approxPolyDP(c, 0.004 * cv2.arcLength(c, True), True)[:, 0, :]
    h, w = mask.shape
    return [[round(float(x) / w, 4), round(float(y) / h, 4)] for x, y in c]


def _png_b64(img: np.ndarray) -> str:
    return base64.b64encode(cv2.imencode(".png", img)[1].tobytes()).decode("utf-8")


def _display_size(h: int, w: int) -> tuple:
    longest = max(h, w)
    s = MIN_DISPLAY / longest if longest < MIN_DISPLAY else min(1.0, MAX_DISPLAY / longest)
    return max(int(round(w * s)), 1), max(int(round(h * s)), 1)


def predict(file_url: str) -> dict:
    image = _load_image(file_url)
    load_model()
    if _session is None:
        return {
            "summary": "LV outline model weights not found, so training has not been completed.",
            "area_fraction": 0.0, "contour": [], "confidence": 0.0,
        }

    dw, dh = _display_size(*image.shape[:2])
    shown = cv2.resize(image, (dw, dh), interpolation=cv2.INTER_CUBIC if dw > image.shape[1] else cv2.INTER_AREA)
    logits = _session.run(["logits"], {"image": _preprocess(image)})[0][0, 0]
    probs = cv2.resize(1.0 / (1.0 + np.exp(-logits)), (dw, dh), interpolation=cv2.INTER_LINEAR)
    mask = largest_component((probs > 0.5).astype(np.uint8))
    area = int(mask.sum())

    if area == 0:
        return {
            "original_image_base64": _png_b64(shown), "overlay_image_base64": _png_b64(shown),
            "mask_base64": _png_b64(np.zeros((dh, dw), np.uint8)),
            "width": dw, "height": dh, "area_fraction": 0.0, "contour": [], "confidence": 0.0,
            "summary": "No clear left ventricle boundary detected in this frame.",
        }

    tint = shown.copy()
    tint[mask > 0] = (255, 160, 60)
    overlay = cv2.addWeighted(shown, 0.65, tint, 0.35, 0)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(overlay, cnts, -1, (255, 255, 255), 2, cv2.LINE_AA)

    return {
        "original_image_base64": _png_b64(shown),
        "overlay_image_base64": _png_b64(overlay),
        "mask_base64": _png_b64(mask * 255),
        "width": dw, "height": dh,
        "area_fraction": round(area / float(dw * dh), 4),
        "contour": contour_points(mask),
        "confidence": round(float(probs[mask > 0].mean()), 3),  # mean model probability inside the outline
        "summary": f"Left ventricle outlined; it covers {100 * area / (dw * dh):.1f}% of the frame.",
    }
