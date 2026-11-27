"""The one number worth trending for each task in this service."""
from typing import Callable, Dict, Optional, Tuple


def _number(value) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _area_percent(result: dict) -> Optional[float]:
    fraction = _number(result.get("area_fraction"))
    return None if fraction is None else round(fraction * 100, 1)


METRICS: Dict[str, Tuple[str, str, Callable[[dict], Optional[float]]]] = {
    "lv-outline": ("LV share of the frame", "%", _area_percent),
}
