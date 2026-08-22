from fastapi import FastAPI

app = FastAPI(title="Reliable Task Engine")

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "API is running"}