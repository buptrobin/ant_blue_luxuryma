"""Main entry point for the marketing agent backend."""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
logger_module = logging.getLogger(__name__)
logger_module.info(f"Loaded environment from: {env_path}")

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
    logger.info("=" * 60)
    logger.info("Starting Marketing Agent API")
    logger.info("=" * 60)

    # Log environment configuration
    ark_api_key = os.getenv("ARK_API_KEY", "")
    ark_base_url = os.getenv("ARK_BASE_URL", "")
    ark_model = os.getenv("ARK_MODEL", "")

    if ark_api_key and ark_base_url:
        logger.info(f"✓ ARK API configured: {ark_model} at {ark_base_url}")
        logger.info(f"✓ API Key: {ark_api_key[:8]}..." if len(ark_api_key) > 8 else "✓ API Key present")
    else:
        logger.warning("⚠ ARK API not configured. Using mock mode.")
        logger.warning(f"  ARK_API_KEY present: {bool(ark_api_key)}")
        logger.warning(f"  ARK_BASE_URL present: {bool(ark_base_url)}")

    # ========== Warmup: Preload resources ==========
    logger.info("🔥 Starting warmup sequence...")

    try:
        # 1. Initialize LLM Manager
        from app.models.llm import get_llm_manager
        logger.info("  [1/3] Initializing LLM Manager...")
        llm_manager = get_llm_manager()
        logger.info(f"  ✓ LLM Manager initialized: {llm_manager.model_type} model")

        # 2. Compile Agent Graph
        from app.agent.graph import get_agent_graph
        logger.info("  [2/3] Compiling Agent Graph...")
        agent_graph = get_agent_graph()
        logger.info("  ✓ Agent Graph compiled with 5 nodes")

        # 3. Initialize Session Manager
        from app.core.session import get_session_manager
        logger.info("  [3/3] Initializing Session Manager...")
        session_manager = get_session_manager()
        logger.info("  ✓ Session Manager initialized")

        logger.info("🚀 Warmup completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Warmup failed: {e}", exc_info=True)
        logger.warning("⚠ Application will continue but may experience slower first request")
        logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("=" * 60)
    logger.info("Shutting down Marketing Agent API")
    logger.info("=" * 60)


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
    "http://10.1.6.170:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for easier LAN access
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
    is_dev = os.getenv("ENVIRONMENT", "development") == "development"

    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=is_dev and os.name != 'nt',  # 在Windows上禁用自动重载
        reload_dirs=["app"] if is_dev else [],
    )


if __name__ == "__main__":
    main()
