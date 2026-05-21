from fastapi import APIRouter

from app.config import settings


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/config")
def health_config():
    translation_provider = (settings.translation_provider or "").strip().lower() or "not_set"
    if translation_provider not in {"groq", "argos", "disabled"}:
        translation_provider = "disabled"

    ai_provider = "groq" if settings.groq_api_key else "fallback"
    environment = getattr(settings, "environment", None) or "not_set"

    return {
        "groq_configured": bool(settings.groq_api_key),
        "translation_provider": translation_provider,
        "ai_provider": ai_provider,
        "database_url_configured": bool(settings.database_url),
        "environment": environment,
    }
