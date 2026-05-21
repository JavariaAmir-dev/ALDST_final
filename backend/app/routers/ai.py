from fastapi import APIRouter, Depends

from app import models, schemas
from app.dependencies import get_current_user
from app.services.ai_service import generate_study_material


router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/preview")
def preview_ai(
    payload: schemas.SessionCreate,
    current_user: models.User = Depends(get_current_user),
):
    return generate_study_material(payload.original_text, payload.reading_style)
