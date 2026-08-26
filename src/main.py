from fastapi import FastAPI, Request
from src.api import tasks
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Reliable Task Engine")

@app.middleware("http")
async def add_process_time_header(request:Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Method: {request.method} Path: {request.url.path} Status: {response.status_code} Latency: {process_time:.4f}s")
    
    return response

app.include_router(tasks.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "API is running"}