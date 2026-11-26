import secrets
from fastapi import Header, HTTPException
from app.config import get_settings

async def require_api_key(x_orchestrator_key: str | None = Header(default=None)) -> None:
    expected = get_settings().orchestrator_api_key.get_secret_value()
    if not expected:
        raise HTTPException(status_code=503, detail='Server authentication is not configured.')
    if not x_orchestrator_key or not secrets.compare_digest(x_orchestrator_key, expected):
        raise HTTPException(status_code=401, detail='Invalid orchestrator credentials.')
