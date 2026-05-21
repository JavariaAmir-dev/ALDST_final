import json

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app import models, schemas
from app.services.ai_service import clean_text, generate_human_flashcards, generate_study_material


def serialize_session(session: models.StudySession) -> schemas.SessionOut:
    raw_quiz = json.loads(session.quiz_questions)
    output_bundle = raw_quiz if isinstance(raw_quiz, dict) else {}
    raw_cards = output_bundle.get("flashcards", raw_quiz)
    flashcards = []
    for item in raw_cards:
        if not isinstance(item, dict) or not item.get("question") or not item.get("answer"):
            continue
        question = clean_text(item["question"])
        answer = clean_text(item["answer"])
        if len(question.split()) >= 5 and len(answer.split()) >= 4 and "supposethat" not in question.lower():
            flashcards.append({
                "question": question if question.endswith("?") else f"{question.rstrip('.!')}?",
                "answer": answer,
                "difficulty": item.get("difficulty", "easy"),
            })
    if not flashcards:
        flashcards = [
            {key: card[key] for key in ("question", "answer", "difficulty")}
            for card in generate_human_flashcards(session.original_text, limit=8)
        ]
    quiz_questions = [card["question"] for card in flashcards]
    return schemas.SessionOut(
        id=session.id,
        title=clean_text(session.title),
        original_text=clean_text(session.original_text),
        simplified_text=clean_text(session.simplified_text),
        summary=clean_text(session.summary),
        audio_friendly_text=clean_text(output_bundle.get("audio_friendly_text", session.summary)),
        translation_friendly_text=clean_text(output_bundle.get("translation_friendly_text", session.simplified_text)),
        flashcards=flashcards,
        key_points=[clean_text(point) for point in json.loads(session.key_points)],
        quiz_questions=quiz_questions,
        reading_style=session.reading_style,
        completed=session.completed,
        created_at=session.created_at,
        progress=session.progress,
    )


def persist_generated_session(
    db: Session,
    current_user: models.User,
    title: str,
    original_text: str,
    reading_style: str,
) -> models.StudySession:
    generated = generate_study_material(original_text, reading_style)
    output_bundle = {
        "flashcards": generated["flashcards"],
        "quiz_questions": generated["quiz_questions"],
        "audio_friendly_text": generated["audio_friendly_text"],
        "translation_friendly_text": generated["translation_friendly_text"],
    }
    session = models.StudySession(
        user_id=current_user.id,
        title=title,
        original_text=original_text,
        simplified_text=generated["simplified_text"],
        summary=generated["summary"],
        key_points=json.dumps(generated["key_points"]),
        quiz_questions=json.dumps(output_bundle),
        reading_style=reading_style,
    )
    db.add(session)
    db.flush()
    db.add(models.ReadingProgress(session_id=session.id, total_chunks=max(len(generated["flashcards"]), 1)))
    db.commit()
    db.refresh(session)
    return session


def session_query(db: Session, user_id: int):
    return db.query(models.StudySession).options(selectinload(models.StudySession.progress)).filter_by(user_id=user_id)


def list_user_sessions(
    db: Session,
    user_id: int,
    q: str | None = None,
    completed: bool | None = None,
    skip: int = 0,
    limit: int = 25,
) -> list[models.StudySession]:
    query = session_query(db, user_id)
    if q:
        search = f"%{q.strip()}%"
        query = query.filter(or_(models.StudySession.title.ilike(search), models.StudySession.original_text.ilike(search)))
    if completed is not None:
        query = query.filter(models.StudySession.completed == completed)
    return query.order_by(models.StudySession.updated_at.desc(), models.StudySession.created_at.desc()).offset(skip).limit(limit).all()
