from io import BytesIO

from fastapi import HTTPException, Response

from app import schemas
from app.services.ai_service import clean_text


def _safe_filename(title: str, extension: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in ("-", "_") else "-" for char in title.strip())
    return f"{cleaned[:70] or 'aldst-session'}.{extension}"


def _text_export(session: schemas.SessionOut) -> str:
    lines = [
        clean_text(session.title),
        "",
        "Summary",
        clean_text(session.summary),
        "",
        "Simplified Notes",
        clean_text(session.simplified_text),
        "",
        "Key Points",
        *[f"- {clean_text(point)}" for point in session.key_points],
        "",
        "Flashcards",
    ]
    for index, card in enumerate(session.flashcards, start=1):
        lines.append(f"{index}. Q: {clean_text(card.question)}")
        lines.append(f"   A: {clean_text(card.answer)}")
    lines.append("")
    lines.append("Quiz Questions")
    lines.extend(f"- {clean_text(question)}" for question in session.quiz_questions)
    return "\n".join(lines)


def _markdown_export(session: schemas.SessionOut) -> str:
    lines = [
        f"# {clean_text(session.title)}",
        "",
        "## Summary",
        clean_text(session.summary),
        "",
        "## Simplified Notes",
        clean_text(session.simplified_text),
        "",
        "## Key Points",
        *[f"- {clean_text(point)}" for point in session.key_points],
        "",
        "## Flashcards",
    ]
    for index, card in enumerate(session.flashcards, start=1):
        lines.append(f"### Card {index}")
        lines.append(f"**Question:** {clean_text(card.question)}")
        lines.append(f"**Answer:** {clean_text(card.answer)}")
        lines.append("")
    lines.append("## Quiz Questions")
    lines.extend(f"- {clean_text(question)}" for question in session.quiz_questions)
    return "\n".join(lines)


def _pdf_export(session: schemas.SessionOut) -> bytes:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="PDF export is not installed on the backend.") from exc

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=clean_text(session.title))
    styles = getSampleStyleSheet()
    story = [Paragraph(clean_text(session.title), styles["Title"]), Spacer(1, 12)]
    for heading, body in (
        ("Summary", clean_text(session.summary)),
        ("Simplified Notes", clean_text(session.simplified_text).replace("\n", "<br/>")),
        ("Key Points", "<br/>".join(f"- {clean_text(point)}" for point in session.key_points)),
    ):
        story.append(Paragraph(heading, styles["Heading2"]))
        story.append(Paragraph(body or "None", styles["BodyText"]))
        story.append(Spacer(1, 10))
    story.append(Paragraph("Flashcards", styles["Heading2"]))
    for index, card in enumerate(session.flashcards, start=1):
        story.append(Paragraph(f"Card {index}: {clean_text(card.question)}", styles["Heading3"]))
        story.append(Paragraph(clean_text(card.answer), styles["BodyText"]))
        story.append(Spacer(1, 8))
    doc.build(story)
    return buffer.getvalue()


def build_export_response(session: schemas.SessionOut, export_format: str) -> Response:
    normalized = export_format.lower()
    if normalized == "txt":
        content = _text_export(session)
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{_safe_filename(session.title, "txt")}"'},
        )
    if normalized in {"md", "markdown"}:
        content = _markdown_export(session)
        return Response(
            content=content,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{_safe_filename(session.title, "md")}"'},
        )
    if normalized == "pdf":
        content = _pdf_export(session)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{_safe_filename(session.title, "pdf")}"'},
        )
    raise HTTPException(status_code=400, detail="Export format must be txt, md, or pdf.")
