from fastapi import FastAPI
from app.api.routes import chat, health, providers
from app.config import get_settings
from app.observability.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
app = FastAPI(title='WHAPPNUS AI ORCHESTRATOR', version='0.1.0', description='Independent multi-provider AI orchestration API.')
app.include_router(health.router)
app.include_router(providers.router, prefix='/v1')
app.include_router(chat.router, prefix='/v1')
