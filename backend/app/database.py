from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_database_schema():
    inspector = inspect(engine)
    if "translations" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("translations")}
    if "target_language" in columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE translations ADD COLUMN target_language VARCHAR(50)"))
        if "language" in columns:
            connection.execute(text("UPDATE translations SET target_language = language WHERE target_language IS NULL"))
