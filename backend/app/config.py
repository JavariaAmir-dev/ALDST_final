from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./aldst.db"
    secret_key: str = "change-this-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    frontend_origin: str = "http://localhost:5173"
    hf_api_token: str | None = None
    hf_model: str = "Qwen/Qwen2.5-7B-Instruct"
    hf_tts_model: str = "facebook/mms-tts-eng"
    use_hf_ai: bool = False
    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"
    translation_provider: str | None = None

    @property
    def frontend_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]
        return origins or ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
