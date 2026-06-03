import base64
import hashlib
import hmac
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings


class RecallService:
    def __init__(self) -> None:
        self.api_key = settings.recall_api_key
        self.base_url = f"https://{settings.recall_region}.recall.ai/api/v1"

    def create_bot(self, meeting_url: str, bot_name: str = "TALON Assistant") -> dict[str, Any]:
        if not self.api_key:
            return {
                "id": None,
                "status": "configuration_required",
                "message": "RECALL_API_KEY is not configured. Meeting was saved, but no bot was sent.",
            }

        payload = {
            "meeting_url": meeting_url,
            "bot_name": bot_name,
            "recording_config": {"transcript": {"provider": {"meeting_captions": {}}}},
        }
        webhook_url = f"{settings.public_backend_url.rstrip('/')}/webhooks/recall"
        payload["real_time_transcription"] = {
            "destination_url": webhook_url,
            "partial_results": False,
        }
        return self._post("/bot/", payload)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Recall.ai request failed with {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Recall.ai request failed: {exc.reason}") from exc


def verify_recall_signature(headers: dict[str, str], payload: bytes) -> bool:
    secret = settings.recall_webhook_secret
    if not secret:
        return settings.environment == "development"

    lower_headers = {key.lower(): value for key, value in headers.items()}
    msg_id = lower_headers.get("webhook-id") or lower_headers.get("svix-id")
    msg_timestamp = lower_headers.get("webhook-timestamp") or lower_headers.get("svix-timestamp")
    msg_signature = lower_headers.get("webhook-signature") or lower_headers.get("svix-signature")
    if not msg_id or not msg_timestamp or not msg_signature:
        return False

    key_material = secret.removeprefix("whsec_")
    try:
        key = base64.b64decode(key_material)
    except Exception:
        key = secret.encode("utf-8")

    signed_content = f"{msg_id}.{msg_timestamp}.{payload.decode('utf-8')}".encode("utf-8")
    expected = base64.b64encode(hmac.new(key, signed_content, hashlib.sha256).digest()).decode("utf-8")
    signatures = [part.split(",", 1)[-1] for part in msg_signature.split(" ")]
    return any(hmac.compare_digest(expected, signature) for signature in signatures)
