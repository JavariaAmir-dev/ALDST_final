from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_current_user


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.get("/preferences", response_model=schemas.PreferenceOut)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    preference = db.query(models.UserPreference).filter_by(user_id=current_user.id).first()
    if not preference:
        preference = models.UserPreference(user_id=current_user.id)
        db.add(preference)
        db.commit()
        db.refresh(preference)
    return preference

@router.put("/preferences", response_model=schemas.PreferenceOut)
def update_preferences(
    payload: schemas.PreferenceBase,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    preference = db.query(models.UserPreference).filter_by(user_id=current_user.id).first()
    if not preference:
        preference = models.UserPreference(user_id=current_user.id)
        db.add(preference)
    preference.preferred_language = payload.preferred_language
    preference.font_size = payload.font_size
    preference.reading_style = payload.reading_style
    db.commit()
    db.refresh(preference)
    return preference
