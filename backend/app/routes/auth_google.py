from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models
from app.db.database import get_db
from app.services import google_calendar_service
from app.services.token_crypto import encrypt_token

router = APIRouter(prefix="/auth/google", tags=["google-auth"])


@router.get("/start")
def google_oauth_start():
    # TODO: Bind state to the logged-in user's server session when auth is added.
    state = f"dev-user:{settings.default_coach_id}"
    try:
        authorization_url = google_calendar_service.build_authorization_url(state)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return RedirectResponse(authorization_url)


@router.get("/callback")
def google_oauth_callback(request: Request, db: Session = Depends(get_db)):
    if "error" in request.query_params:
        return RedirectResponse(f"{settings.frontend_url.rstrip()}/settings?calendar=error")

    # TODO: Replace this development coach with the authenticated user.
    user_id = settings.default_coach_id
    try:
        credentials = google_calendar_service.exchange_callback(str(request.url))
        email = google_calendar_service.primary_calendar_email(credentials)
        active_connections = db.scalars(
            select(models.CalendarConnection)
            .where(models.CalendarConnection.user_id == user_id)
            .where(models.CalendarConnection.provider == "google")
            .where(models.CalendarConnection.is_active.is_(True))
        ).all()
        for connection in active_connections:
            connection.is_active = False

        db.add(
            models.CalendarConnection(
                user_id=user_id,
                provider="google",
                google_account_email=email,
                access_token_encrypted=encrypt_token(credentials.token),
                refresh_token_encrypted=encrypt_token(credentials.refresh_token) if credentials.refresh_token else None,
                token_expiry=credentials.expiry,
                scopes=list(credentials.scopes or settings.google_scopes),
                is_active=True,
            )
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Google OAuth failed: {exc}") from exc

    return RedirectResponse(f"{settings.frontend_url.rstrip('/')}/settings?calendar=connected")
