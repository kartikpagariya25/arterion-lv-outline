# Model card: Arterion LV Outline

> Research prototype, not a medical device. Do not use for diagnosis or treatment decisions.

## Task
Left-ventricle segmentation on an apical four-chamber echocardiogram frame.

## Model
ResNet-34 U-Net (24.4 M parameters) trained with Dice + focal-Tversky loss on masks rasterised from expert tracings.

## Input and output
- **Input:** one echocardiogram frame (image).
- **Output:** mask, tinted overlay, a simplified outline polygon, area fraction and a mean-probability confidence.

## Training and evaluation data
EchoNet-Dynamic expert LV tracings (Ouyang et al., Nature 2020); test split of 2,552 frames.

## Results
- Dice 0.925, IoU 0.863, precision 0.923, recall 0.933 per frame.

Numbers in `training/artifacts/metrics.json` match the published weights.

## Limitations
- Evaluated only on end-diastolic and end-systolic frames that carry expert tracings.
- Single-centre apical four-chamber views; other views, poor windows or other scanners may trace the wrong cavity.
- Confidence is the mean probability inside the outline, not a calibrated probability.

## Intended use
Research, teaching and prototyping. Not for diagnosis, triage or any clinical decision, and not validated for any clinical setting.

## Licence and data terms
Code: MIT. EchoNet-Dynamic is for non-commercial research use only.
