# Arterion LV Outline

Traces the **left ventricle** on an apical four-chamber echocardiogram frame: a binary mask, a tinted overlay, and a simplified outline polygon you can feed into volume or ejection-fraction calculations. The site draws the outline with an animated pen stroke and can pick a frame straight from a video.

![Screenshot](docs/screenshot.jpg)

> **Research prototype — not a medical device.**

Part of the [Arterion](https://github.com/kartikpagariya25/Arterion) project.

## How it works

A ResNet-34 **U-Net** (24.4 M parameters), trained with Dice + focal-Tversky loss on masks rasterised from the EchoNet-Dynamic expert LV tracings (`training/src/build_masks.py`). Input is resized to 112×112, the mask is upsampled with the probabilities (smooth edges) and only the **largest connected region** is kept. The returned `confidence` is the model's mean probability inside the outline.

## Results (EchoNet-Dynamic test split, 2,552 frames)

| Dice | IoU | Precision | Recall |
|---|---|---|---|
| **0.925** | 0.863 | 0.923 | 0.933 |

Evaluated per frame on the end-diastolic / end-systolic frames that carry expert tracings. Trained on one centre's apical four-chamber views; other views, poor acoustic windows or other scanners may fail or trace the wrong cavity.

## Run it

```bash
./scripts/fetch_weights.sh        # or .\scripts\fetch_weights.ps1  (GitHub Release)
docker compose up --build
# site: http://localhost:8080     API docs: http://localhost:8000/docs
```

Without Docker: `cd backend && pip install -r requirements-dev.txt && uvicorn app.main:app --port 8000`, then serve `frontend/`. The site talks to `window.API_BASE` (`frontend/js/config.js`). No sample images are bundled: the EchoNet-Dynamic data-use terms do not allow redistributing its frames.

### API

| Endpoint | Body | Returns |
|---|---|---|
| `POST /uploads` | multipart `file` | `{file_url}` |
| `POST /lv-outline/predict` | `{file_url}` (image) | `original_image_base64`, `overlay_image_base64`, `mask_base64`, `contour` (normalised polygon), `area_fraction`, `confidence`, `width`, `height` |

Small frames are upscaled to 448 px for display and large ones capped at 640 px. Non-images return 422; a frame with no ventricle returns an empty contour and a clear summary.

Tests: `cd backend && pytest tests`.

## Training

`training/src`: `build_masks.py` → `train.py` → `evaluate.py` → `export_onnx.py` → `infer.py`. The network (`unet.py`) and loss (`losses.py`) are self-contained in this repo.

## Data and licences

Code: MIT. Trained on [EchoNet-Dynamic](https://echonet.github.io/dynamic/) (Ouyang et al., *Nature* 2020), which is released under the Stanford University Dataset Research Use Agreement — non-commercial research use only. Check those terms before using the trained weights outside research.
