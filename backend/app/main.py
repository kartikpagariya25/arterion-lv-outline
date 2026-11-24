from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .common import UPLOAD_DIR, InvalidInput, invalid_input_handler, router as uploads_router
from .lv_outline.router import router as task_router

app = FastAPI(title="arterion-lv-outline")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_exception_handler(InvalidInput, invalid_input_handler)
app.include_router(uploads_router)
app.include_router(task_router)
app.mount("/static_uploads", StaticFiles(directory=UPLOAD_DIR), name="static_uploads")


@app.get("/health")
def health():
    return {"status": "ok"}
