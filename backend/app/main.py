"""
Social Recipe API - FastAPI application.
API contracts align with Android app: same endpoints and JSON field names (snake_case).
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import health, recipe

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=get_settings().app_name,
    description="Backend for SocialRecipeApp. Import and normalize recipes from social links.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(recipe.router)


@app.get("/")
def root():
    return {"service": get_settings().app_name, "docs": "/docs"}
