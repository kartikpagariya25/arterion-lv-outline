from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from ..accounts.deps import optional_user
from ..accounts.history import record_analysis
from .model import predict

router = APIRouter(prefix="/lv-outline", tags=["lv-outline"])


class PredictRequest(BaseModel):
    file_url: str


@router.post("/predict")
def predict_lv(req: PredictRequest, response: Response, user=Depends(optional_user)):
    result = predict(req.file_url)
    record_analysis(user, "lv-outline", req.file_url, result, response)
    return result
