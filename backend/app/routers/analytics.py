from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=schemas.AnalyticsOut)
def analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    sessions = db.query(models.StudySession).options(selectinload(models.StudySession.progress)).filter_by(
        user_id=current_user.id
    ).all()
    session_ids = [session.id for session in sessions]
    translations = []
    if session_ids:
        translations = db.query(models.Translation).filter(models.Translation.session_id.in_(session_ids)).all()

    progress_values = [session.progress.progress_percent for session in sessions if session.progress]
    styles = Counter(session.reading_style for session in sessions)
    languages = Counter(translation.target_language for translation in translations if translation.target_language)

    return schemas.AnalyticsOut(
        total_sessions=len(sessions),
        completed_sessions=sum(1 for session in sessions if session.completed),
        average_progress=round(sum(progress_values) / len(progress_values), 1) if progress_values else 0,
        most_used_reading_style=styles.most_common(1)[0][0] if styles else "simple",
        most_used_translation_language=languages.most_common(1)[0][0] if languages else "None yet",
    )
