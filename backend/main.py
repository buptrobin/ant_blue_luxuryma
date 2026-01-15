"""Main entry point for the marketing agent backend."""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage FastAPI lifespan (startup/shutdown)."""
    # Startup
    logger.info("Starting Marketing Agent API")
    yield
    # Shutdown
    logger.info("Shutting down Marketing Agent API")


# Create FastAPI app
app = FastAPI(
    title=os.getenv("API_TITLE", "Marketing Agent API"),
    version=os.getenv("API_VERSION", "v1"),
    description="AI-powered marketing audience segmentation agent",
    lifespan=lifespan
)

# Add CORS middleware
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": "Marketing Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


def main():
    """Run the FastAPI server."""
    import uvicorn

    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")

    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT", "development") == "development"
    )


if __name__ == "__main__":
    main()
