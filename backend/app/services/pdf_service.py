from fastapi import HTTPException, UploadFile

from app.services.ai_service import clean_text


MAX_PDF_BYTES = 10 * 1024 * 1024


async def extract_pdf_text(file: UploadFile) -> str:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded PDF is empty.")
    if len(content) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF size must be 10 MB or smaller.")

    try:
        from pypdf import PdfReader
        from io import BytesIO

        reader = PdfReader(BytesIO(content))
        pages = [(page.extract_text() or "").strip() for page in reader.pages[:25]]
        text = clean_text("\n\n".join(page for page in pages if page))
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="PDF support is not installed. Run pip install -r requirements.txt.",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not read text from this PDF.") from exc

    if len(text.strip()) < 20:
        raise HTTPException(
            status_code=400,
            detail="No readable text was found. Scanned image PDFs need OCR before upload.",
        )
    return text[:5000]
