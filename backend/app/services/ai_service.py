import json
from typing import Any

from openai import OpenAI

from app.core.config import settings


class AIService:
    def __init__(self) -> None:
        self.model = settings.openai_model
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def structured_completion(self, system: str, prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
        if not self.client:
            return fallback

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
            )
            content = response.choices[0].message.content or "{}"
            result = json.loads(content)
            result["_usage"] = {
                "model": self.model,
                "tokens_used": response.usage.total_tokens if response.usage else None,
            }
            return result
        except Exception as exc:
            fallback["warning"] = f"AI provider unavailable, returned local structured fallback: {exc}"
            return fallback

