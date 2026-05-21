from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sessions: Mapped[list["StudySession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    preferences: Mapped["UserPreference"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    preferred_language: Mapped[str] = mapped_column(String(50), default="English")
    font_size: Mapped[int] = mapped_column(Integer, default=18)
    reading_style: Mapped[str] = mapped_column(String(40), default="simple")

    user: Mapped[User] = relationship(back_populates="preferences")


class StudySession(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    original_text: Mapped[str] = mapped_column(Text)
    simplified_text: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)
    key_points: Mapped[str] = mapped_column(Text)
    quiz_questions: Mapped[str] = mapped_column(Text)
    reading_style: Mapped[str] = mapped_column(String(40), default="simple")
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="sessions")
    progress: Mapped["ReadingProgress"] = relationship(back_populates="session", cascade="all, delete-orphan", uselist=False)
    translations: Mapped[list["Translation"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    audio_files: Mapped[list["AudioFile"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class ReadingProgress(Base):
    __tablename__ = "reading_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), unique=True)
    current_chunk: Mapped[int] = mapped_column(Integer, default=0)
    total_chunks: Mapped[int] = mapped_column(Integer, default=1)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session: Mapped[StudySession] = relationship(back_populates="progress")


class Translation(Base):
    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_language: Mapped[str] = mapped_column(String(50))
    translated_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped[StudySession] = relationship(back_populates="translations")


class AudioFile(Base):
    __tablename__ = "audio_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)
    voice: Mapped[str] = mapped_column(String(50), default="calm")
    audio_url: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped[StudySession] = relationship(back_populates="audio_files")
