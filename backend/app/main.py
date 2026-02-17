"""
FastAPI application entry point for BharatScheme-AI.
"""

from fastapi import FastAPI
import uvicorn

from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.schemes import router as schemes_router

app = FastAPI(title="BharatScheme-AI")

app.include_router(chat_router, prefix="/api/v1")
app.include_router(schemes_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"status": "online"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
