from fastapi import APIRouter, Depends, HTTPException
import json
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services.audio_service import generate_audio_reference


router = APIRouter(prefix="/audio", tags=["audio"])


@router.post("", response_model=schemas.AudioOut)
def create_audio(
    payload: schemas.AudioCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    session = db.query(models.StudySession).filter_by(id=payload.session_id, user_id=current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    audio = models.AudioFile(
        session_id=session.id,
        voice=payload.voice,
        audio_url=generate_audio_reference(session.id, payload.voice),
    )
    db.add(audio)
    db.commit()
    db.refresh(audio)
    output_bundle = json.loads(session.quiz_questions)
    audio_script = output_bundle.get("audio_friendly_text", session.summary) if isinstance(output_bundle, dict) else session.summary
    return schemas.AudioOut(
        id=audio.id,
        session_id=audio.session_id,
        voice=audio.voice,
        audio_url=audio.audio_url,
        audio_script=audio_script,
        created_at=audio.created_at,
    )
