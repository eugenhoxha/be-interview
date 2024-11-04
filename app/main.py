"""
This FastAPI application serves as the entry point for the application. 
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import api_router
from app.logger import logger

app = FastAPI(
    title="Organisation locations API",
    description="Initial API version of organisation locations",
    version="1.0.0",
)

app.include_router(api_router, prefix="/api")

@app.get("/health", response_class=JSONResponse)
async def health_check(request: Request):
    """
    Health check function.
    """

    return JSONResponse({"status": "ok"})

@app.on_event("startup")
async def startup_event():
    """
    Startup event to run the initial cleanup and start the periodic cleanup loop.
    """

    logger.info("Application startup complete.")

@app.on_event("shutdown")
def shutdown_event():
    """
    Shutdown event to perform any cleanup if necessary.
    """
    logger.info("Application shutdown.")