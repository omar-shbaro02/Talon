import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models
from app.services.token_crypto import decrypt_token, encrypt_token


def google_client_config() -> dict[str, Any]:
    if not settings.google_client_id or not settings.google_client_secret:
        raise RuntimeError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are required")
    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }


def build_authorization_url(state: str) -> str:
    if settings.environment == "development":
        os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        google_client_config(),
        scopes=settings.google_scopes,
        redirect_uri=settings.google_redirect_uri,
    )
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return authorization_url


def exchange_callback(authorization_response: str):
    if settings.environment == "development":
        os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        google_client_config(),
        scopes=settings.google_scopes,
        redirect_uri=settings.google_redirect_uri,
    )
    flow.fetch_token(authorization_response=authorization_response)
    return flow.credentials


def credentials_from_connection(connection: models.CalendarConnection):
    from google.oauth2.credentials import Credentials

    return Credentials(
        token=decrypt_token(connection.access_token_encrypted),
        refresh_token=decrypt_token(connection.refresh_token_encrypted) if connection.refresh_token_encrypted else None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=connection.scopes or settings.google_scopes,
    )


def refresh_if_needed(db: Session, connection: models.CalendarConnection):
    from google.auth.transport.requests import Request

    credentials = credentials_from_connection(connection)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        connection.access_token_encrypted = encrypt_token(credentials.token)
        if credentials.expiry:
            connection.token_expiry = credentials.expiry
        db.flush()
    return credentials


def calendar_service(credentials):
    from googleapiclient.discovery import build

    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


def create_google_event(credentials, payload, calendar_id: str = "primary") -> dict[str, Any]:
    service = calendar_service(credentials)
    body = event_body(payload)
    return (
        service.events()
        .insert(calendarId=calendar_id, body=body, conferenceDataVersion=1 if payload.add_google_meet else 0)
        .execute()
    )


def update_google_event(credentials, google_event_id: str, payload, calendar_id: str = "primary") -> dict[str, Any]:
    service = calendar_service(credentials)
    body = event_body(payload)
    return (
        service.events()
        .patch(calendarId=calendar_id, eventId=google_event_id, body=body, conferenceDataVersion=1 if getattr(payload, "add_google_meet", False) else 0)
        .execute()
    )


def delete_google_event(credentials, google_event_id: str, calendar_id: str = "primary") -> None:
    service = calendar_service(credentials)
    service.events().delete(calendarId=calendar_id, eventId=google_event_id).execute()


def event_body(payload) -> dict[str, Any]:
    body = {
        "summary": payload.title,
        "description": payload.description or "",
        "location": payload.location or "",
        "start": {"dateTime": payload.start_time.isoformat(), "timeZone": payload.timezone},
        "end": {"dateTime": payload.end_time.isoformat(), "timeZone": payload.timezone},
        "attendees": [{"email": email} for email in payload.attendees],
    }
    if payload.add_google_meet:
        body["conferenceData"] = {
            "createRequest": {
                "requestId": f"talon-{uuid4()}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        }
    return body


def extract_meet_link(event: dict[str, Any]) -> str | None:
    if event.get("hangoutLink"):
        return event["hangoutLink"]
    for entry in event.get("conferenceData", {}).get("entryPoints", []) or []:
        if entry.get("entryPointType") == "video":
            return entry.get("uri")
    return None


def primary_calendar_email(credentials) -> str | None:
    try:
        calendar = calendar_service(credentials).calendarList().get(calendarId="primary").execute()
        return calendar.get("id")
    except Exception:
        return None


def token_expired(connection: models.CalendarConnection) -> bool:
    return bool(connection.token_expiry and connection.token_expiry.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc))
