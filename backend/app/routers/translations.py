from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services.session_service import serialize_session
from app.services.translation_service import TranslationError, translate_text


router = APIRouter(prefix="/translations", tags=["translations"])


def build_study_material_for_translation(session: models.StudySession) -> str:
    serialized = serialize_session(session)
    flashcards = "\n".join(
        f"- Q: {card.question}\n  A: {card.answer}" for card in serialized.flashcards
    )
    quiz_questions = "\n".join(f"- {question}" for question in serialized.quiz_questions)
    key_points = "\n".join(f"- {point}" for point in serialized.key_points)
    return "\n\n".join(
        [
            f"Title:\n{serialized.title}",
            f"Simplified Notes:\n{serialized.translation_friendly_text or serialized.simplified_text}",
            f"Short Summary:\n{serialized.summary}",
            f"Key Points:\n{key_points}",
            f"Flashcards:\n{flashcards}",
            f"Quiz Questions:\n{quiz_questions}",
        ]
    )


@router.post("", response_model=schemas.TranslationOut)
def create_translation(
    payload: schemas.TranslationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    session = db.query(models.StudySession).filter_by(id=payload.session_id, user_id=current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    source_text = build_study_material_for_translation(session)
    try:
        translated_text = f"Translated Study Material:\n\n{translate_text(source_text, payload.target_language)}"
    except TranslationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    translation = models.Translation(
        session_id=session.id,
        language=payload.target_language,
        target_language=payload.target_language,
        translated_text=translated_text,
    )
    db.add(translation)
    db.commit()
    db.refresh(translation)
    return translation
