from app.services.ai_service import AIService


class ContentAgent:
    name = "ContentAgent"

    def __init__(self, ai: AIService) -> None:
        self.ai = ai

    def generate(self, content_type: str, topic: str, tone: str, context: str | None = None) -> dict:
        fallback = {
            "title": f"{topic}: {content_type.replace('_', ' ').title()}",
            "content": (
                f"Here is a {tone} {content_type.replace('_', ' ')} on {topic}.\n\n"
                "Open with the leadership tension, make the idea practical, and close with a clear reflection prompt or next action."
            ),
            "format_notes": ["Designed for a coach/trainer audience", "Ready for light editing before publishing"],
        }
        return self.ai.structured_completion(
            "You are TALON's content studio agent. Return strict JSON with title, content, and format_notes.",
            f"Type: {content_type}\nTopic: {topic}\nTone: {tone}\nContext:\n{context or 'None'}",
            fallback,
        )

