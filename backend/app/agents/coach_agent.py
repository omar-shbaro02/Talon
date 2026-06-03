from app.services.ai_service import AIService


class CoachAgent:
    name = "CoachAgent"

    def __init__(self, ai: AIService) -> None:
        self.ai = ai

    def analyze(self, prompt: str, context: str | None = None) -> dict:
        fallback = {
            "analysis": "The client appears to need clearer prioritization, stronger reflection loops, and a practical accountability structure.",
            "suggested_questions": [
                "What outcome would make the next session unmistakably valuable?",
                "Where is the client avoiding a difficult but necessary conversation?",
                "Which behavior would create visible progress within seven days?",
            ],
            "recommended_framework": "GROW model with a short stakeholder-mapping exercise",
            "risks_or_blockers": ["Ambiguous goals", "Competing executive priorities", "Low follow-through cadence"],
            "next_steps": ["Clarify the desired business outcome", "Define one measurable commitment", "Schedule a progress check-in"],
        }
        return self.ai.structured_completion(
            "You are TALON's executive coaching agent. Return strict JSON with analysis, suggested_questions, recommended_framework, risks_or_blockers, next_steps.",
            f"Prompt: {prompt}\n\nContext:\n{context or 'No extra context'}",
            fallback,
        )

