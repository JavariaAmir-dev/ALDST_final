from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.database import Base, engine, ensure_database_schema
from app.routers import ai, analytics, audio, auth, health, sessions, translations, users


configure_logging()
Base.metadata.create_all(bind=engine)
ensure_database_schema()

app = FastAPI(title="ALDST API", version="1.0.0")
register_error_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys([*settings.frontend_origins, "http://localhost:5173", "http://127.0.0.1:5173"])),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(translations.router, prefix="/api")
app.include_router(audio.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
