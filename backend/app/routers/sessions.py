from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session, selectinload

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services.export_service import build_export_response
from app.services.pdf_service import extract_pdf_text
from app.services.session_service import list_user_sessions, persist_generated_session, serialize_session


router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=schemas.SessionOut)
def create_session(
    payload: schemas.SessionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    session = persist_generated_session(db, current_user, payload.title, payload.original_text, payload.reading_style)
    return serialize_session(session)


@router.post("/from-pdf", response_model=schemas.SessionOut)
async def create_session_from_pdf(
    title: str = Form(..., min_length=1, max_length=160),
    reading_style: str = Form("simple"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    original_text = await extract_pdf_text(file)
    session = persist_generated_session(db, current_user, title, original_text, reading_style)
    return serialize_session(session)


@router.get("", response_model=list[schemas.SessionOut])
def list_sessions(
    q: str | None = Query(default=None, max_length=80),
    completed: bool | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    sessions = list_user_sessions(db, current_user.id, q=q, completed=completed, skip=skip, limit=limit)
    return [serialize_session(session) for session in sessions]


@router.get("/last-active", response_model=schemas.SessionOut)
def get_last_active_session(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    session = db.query(models.StudySession).options(selectinload(models.StudySession.progress)).filter_by(
        user_id=current_user.id
    ).order_by(models.StudySession.updated_at.desc(), models.StudySession.created_at.desc()).first()
    if not session:
        raise HTTPException(status_code=404, detail="No study sessions yet")
    return serialize_session(session)


@router.get("/{session_id}", response_model=schemas.SessionOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    session = db.query(models.StudySession).options(selectinload(models.StudySession.progress)).filter_by(
        id=session_id, user_id=current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return serialize_session(session)


@router.get("/{session_id}/export")
def export_session(
    session_id: int,
    format: str = Query(default="txt", pattern="^(txt|md|markdown|pdf)$"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    session = db.query(models.StudySession).options(selectinload(models.StudySession.progress)).filter_by(
        id=session_id, user_id=current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return build_export_response(serialize_session(session), format)


@router.put("/{session_id}/progress", response_model=schemas.SessionOut)
def update_progress(
    session_id: int,
    payload: schemas.ProgressUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    session = db.query(models.StudySession).options(selectinload(models.StudySession.progress)).filter_by(
        id=session_id, user_id=current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.progress:
        session.progress = models.ReadingProgress(session_id=session.id)

    session.progress.current_chunk = min(payload.current_chunk, payload.total_chunks - 1)
    session.progress.total_chunks = payload.total_chunks
    session.progress.progress_percent = round(((payload.current_chunk + 1) / payload.total_chunks) * 100)
    session.completed = payload.completed
    db.commit()
    db.refresh(session)
    return serialize_session(session)
