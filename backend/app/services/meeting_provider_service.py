import base64
import json
from dataclasses import dataclass
from datetime import timezone
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import settings


@dataclass
class ProviderMeeting:
    provider: str
    link: str
    external_id: str | None = None


def _json_request(url: str, method: str = "GET", headers: dict | None = None, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(detail or str(exc)) from exc


def _form_request(url: str, headers: dict | None = None, payload: dict | None = None) -> dict:
    data = urlencode(payload or {}).encode("utf-8")
    request = Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded", **(headers or {})},
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(detail or str(exc)) from exc


def create_zoom_meeting(payload) -> ProviderMeeting:
    if not settings.zoom_account_id or not settings.zoom_client_id or not settings.zoom_client_secret:
        raise RuntimeError("Zoom is not configured. Set ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, and ZOOM_CLIENT_SECRET.")

    auth = base64.b64encode(f"{settings.zoom_client_id}:{settings.zoom_client_secret}".encode("utf-8")).decode("ascii")
    token_response = _form_request(
        f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={settings.zoom_account_id}",
        headers={"Authorization": f"Basic {auth}"},
    )
    access_token = token_response.get("access_token")
    if not access_token:
        raise RuntimeError("Zoom did not return an access token.")

    zoom_user_id = settings.zoom_user_id or "me"
    meeting = _json_request(
        f"https://api.zoom.us/v2/users/{zoom_user_id}/meetings",
        method="POST",
        headers={"Authorization": f"Bearer {access_token}"},
        payload={
            "topic": payload.title,
            "type": 2,
            "start_time": payload.start_time.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "duration": max(1, int((payload.end_time - payload.start_time).total_seconds() // 60)),
            "timezone": payload.timezone,
            "agenda": payload.description or "",
            "settings": {
                "join_before_host": False,
                "waiting_room": True,
            },
        },
    )
    link = meeting.get("join_url")
    if not link:
        raise RuntimeError("Zoom did not return a join URL.")
    return ProviderMeeting(provider="zoom", link=link, external_id=str(meeting.get("id") or ""))


def create_teams_meeting(payload) -> ProviderMeeting:
    if not settings.teams_user_id:
        raise RuntimeError("Teams is not configured. Set TEAMS_USER_ID to the Microsoft user object ID or UPN that will host meetings.")

    access_token = settings.teams_access_token or _microsoft_access_token()
    endpoint = f"https://graph.microsoft.com/v1.0/users/{settings.teams_user_id}/onlineMeetings"

    meeting = _json_request(
        endpoint,
        method="POST",
        headers={"Authorization": f"Bearer {access_token}"},
        payload={
            "subject": payload.title,
            "startDateTime": payload.start_time.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "endDateTime": payload.end_time.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        },
    )
    link = meeting.get("joinWebUrl")
    if not link:
        raise RuntimeError("Microsoft Graph did not return a Teams join URL.")
    return ProviderMeeting(provider="teams", link=link, external_id=meeting.get("id"))


def _microsoft_access_token() -> str:
    if not settings.microsoft_tenant_id or not settings.microsoft_client_id or not settings.microsoft_client_secret:
        raise RuntimeError(
            "Teams is not configured. Set MICROSOFT_TENANT_ID, MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, "
            "and TEAMS_USER_ID, or provide TEAMS_ACCESS_TOKEN for local testing."
        )

    token_response = _form_request(
        f"https://login.microsoftonline.com/{settings.microsoft_tenant_id}/oauth2/v2.0/token",
        payload={
            "client_id": settings.microsoft_client_id,
            "client_secret": settings.microsoft_client_secret,
            "grant_type": "client_credentials",
            "scope": "https://graph.microsoft.com/.default",
        },
    )
    access_token = token_response.get("access_token")
    if not access_token:
        raise RuntimeError("Microsoft identity platform did not return an access token.")
    return access_token


def zoom_configured() -> bool:
    return bool(settings.zoom_account_id and settings.zoom_client_id and settings.zoom_client_secret)


def teams_configured() -> bool:
    has_app_credentials = bool(settings.microsoft_tenant_id and settings.microsoft_client_id and settings.microsoft_client_secret)
    return bool(settings.teams_user_id and (settings.teams_access_token or has_app_credentials))
