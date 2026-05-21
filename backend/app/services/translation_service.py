from abc import ABC, abstractmethod

import httpx

from app.config import settings
SOURCE_LANGUAGE_CODE = "en"
DISABLED_PROVIDER_MESSAGE = (
    "Translation provider is not configured. Add GROQ_API_KEY or enable local Argos translation."
)

SUPPORTED_TARGET_LANGUAGES = {
    "Urdu": {"argos_code": "ur", "groq_name": "Urdu"},
    "Arabic": {"argos_code": "ar", "groq_name": "Arabic"},
    "French": {"argos_code": "fr", "groq_name": "French"},
    "Spanish": {"argos_code": "es", "groq_name": "Spanish"},
    "German": {"argos_code": "de", "groq_name": "German"},
}

MISSING_MODEL_MESSAGE = (
    "Translation model for this language is not installed. "
    "Please install the language package or choose another language."
)


class TranslationError(Exception):
    status_code = 400

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        super().__init__(message)


class TranslationProvider(ABC):
    @abstractmethod
    def translate(self, text: str, target_language: str) -> str:
        raise NotImplementedError


class DisabledTranslationProvider(TranslationProvider):
    def translate(self, text: str, target_language: str) -> str:
        raise TranslationError(DISABLED_PROVIDER_MESSAGE, status_code=503)


class GroqTranslationProvider(TranslationProvider):
    def translate(self, text: str, target_language: str) -> str:
        target_name = _target_language_value(target_language, "groq_name")
        cleaned_text = _clean_translation_input(text)

        if not settings.groq_api_key:
            raise TranslationError(DISABLED_PROVIDER_MESSAGE, status_code=503)

        payload = {
            "model": settings.groq_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a professional study-material translator. "
                        "Return only the translated study material."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Translate this study material into {target_name}.\n"
                        "Preserve headings, bullets, flashcard Q/A format, and quiz format. "
                        "Keep the language simple and student-friendly. "
                        "Do not add extra explanations.\n\n"
                        f"{cleaned_text}"
                    ),
                },
            ],
            "temperature": 0.1,
            "max_tokens": 2400,
        }
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            translated_text = response.json()["choices"][0]["message"]["content"].strip()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {401, 403}:
                raise TranslationError(DISABLED_PROVIDER_MESSAGE, status_code=503) from exc
            raise TranslationError("Groq translation failed. Please try again later.", status_code=502) from exc
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            raise TranslationError("Groq translation failed. Please try again later.", status_code=502) from exc

        if not translated_text:
            raise TranslationError("Groq did not return translated text. Please try again.", status_code=502)
        return translated_text


class ArgosTranslationProvider(TranslationProvider):
    def translate(self, text: str, target_language: str) -> str:
        target_code = _target_language_value(target_language, "argos_code")
        cleaned_text = _clean_translation_input(text)

        try:
            from argostranslate import translate as argos_translate
        except ImportError as exc:
            raise TranslationError(
                "Argos Translate is not installed on the backend. Install backend requirements and try again."
            ) from exc

        installed_languages = argos_translate.get_installed_languages()
        source_language = _find_language(installed_languages, SOURCE_LANGUAGE_CODE)
        target = _find_language(installed_languages, target_code)
        if not source_language or not target:
            raise TranslationError(MISSING_MODEL_MESSAGE)

        translation = source_language.get_translation(target)
        if not translation:
            raise TranslationError(MISSING_MODEL_MESSAGE)

        translated_chunks = [translation.translate(chunk) for chunk in _split_text(cleaned_text)]
        translated_text = "\n\n".join(chunk.strip() for chunk in translated_chunks if chunk.strip())
        if not translated_text:
            raise TranslationError("Argos Translate did not return translated text. Please try again.")
        return translated_text


def supported_language_names() -> str:
    return ", ".join(SUPPORTED_TARGET_LANGUAGES)


def get_translation_provider() -> TranslationProvider:
    configured_provider = (settings.translation_provider or "").strip().lower()

    if configured_provider == "groq":
        return GroqTranslationProvider() if settings.groq_api_key else DisabledTranslationProvider()
    if configured_provider == "argos":
        return ArgosTranslationProvider()
    if configured_provider == "disabled":
        return DisabledTranslationProvider()
    if configured_provider:
        return DisabledTranslationProvider()
    if settings.groq_api_key:
        return GroqTranslationProvider()
    return DisabledTranslationProvider()


def translate_text(text: str, target_language: str) -> str:
    return get_translation_provider().translate(text, target_language)


def _target_language_value(target_language: str, key: str) -> str:
    language = SUPPORTED_TARGET_LANGUAGES.get(target_language)
    if not language:
        raise TranslationError(
            f"Translation to {target_language} is not supported. Please choose {supported_language_names()}."
        )
    return language[key]


def _clean_translation_input(text: str) -> str:
    cleaned_lines = [" ".join(line.split()) for line in str(text or "").splitlines()]
    cleaned_text = "\n".join(line for line in cleaned_lines if line).strip()
    if not cleaned_text:
        raise TranslationError("There is no generated study material available to translate.")
    return cleaned_text


def _find_language(installed_languages, language_code: str):
    return next((language for language in installed_languages if language.code == language_code), None)


def _split_text(text: str, max_chars: int = 2500) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= max_chars:
            current = paragraph
            continue
        for index in range(0, len(paragraph), max_chars):
            chunks.append(paragraph[index : index + max_chars])
        current = ""
    if current:
        chunks.append(current)
    return chunks or [text[:max_chars]]
