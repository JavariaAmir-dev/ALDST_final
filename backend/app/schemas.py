from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class PreferenceBase(BaseModel):
    preferred_language: str = "English"
    font_size: int = Field(default=18, ge=14, le=28)
    reading_style: str = "simple"


class PreferenceOut(PreferenceBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    original_text: str = Field(min_length=20)
    reading_style: str = "simple"


class ProgressOut(BaseModel):
    current_chunk: int
    total_chunks: int
    progress_percent: int

    class Config:
        from_attributes = True


class FlashcardOut(BaseModel):
    question: str
    answer: str
    difficulty: str = "easy"


class SessionOut(BaseModel):
    id: int
    title: str
    original_text: str
    simplified_text: str
    summary: str
    audio_friendly_text: str = ""
    translation_friendly_text: str = ""
    flashcards: list[FlashcardOut] = Field(default_factory=list)
    key_points: list[str]
    quiz_questions: list[str]
    reading_style: str
    completed: bool
    created_at: datetime
    progress: ProgressOut | None = None

    class Config:
        from_attributes = True


class ProgressUpdate(BaseModel):
    current_chunk: int = Field(ge=0)
    total_chunks: int = Field(ge=1)
    completed: bool = False


class TranslationCreate(BaseModel):
    session_id: int
    target_language: str


class TranslationOut(BaseModel):
    id: int
    session_id: int
    target_language: str
    translated_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class AudioCreate(BaseModel):
    session_id: int
    voice: str = "calm"


class AudioOut(BaseModel):
    id: int
    session_id: int
    voice: str
    audio_url: str
    audio_script: str = ""
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsOut(BaseModel):
    total_sessions: int
    completed_sessions: int
    average_progress: float
    most_used_reading_style: str
    most_used_translation_language: str
