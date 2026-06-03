from app.services.ai_service import AIService


class MeetingAgent:
    name = "MeetingAgent"

    def __init__(self, ai: AIService) -> None:
        self.ai = ai

    def analyze(self, title: str, transcript: str, context: str | None = None) -> dict:
        excerpt = transcript[:240].strip()
        fallback = {
            "summary": f"{title} focused on leadership priorities, current blockers, and concrete follow-up commitments. Key source excerpt: {excerpt}",
            "key_topics": ["Leadership focus", "Execution blockers", "Stakeholder alignment"],
            "action_items": [
                {"title": "Send follow-up recap", "assigned_to": "Coach", "priority": "high"},
                {"title": "Confirm next leadership experiment", "assigned_to": "Client", "priority": "medium"},
            ],
            "decisions": ["Use the next session to convert insights into measurable commitments"],
            "commitments": ["Coach will provide a concise recap and next-step prompts"],
            "coaching_observations": ["Client may benefit from separating urgent tasks from strategic leadership work"],
            "leadership_patterns": ["Balances operational urgency with a need for clearer strategic focus"],
            "emotional_tone": "Focused and reflective",
            "risks_or_blockers": ["Priorities may remain too broad without a named owner and deadline"],
            "recommended_next_steps": ["Draft follow-up email", "Update client profile", "Create one action item for next session"],
            "follow_up_email": "Subject: Session recap and next steps\n\nThank you for the conversation today. Here are the key themes, commitments, and next steps we will carry into our next session.",
        }
        return self.ai.structured_completion(
            "You are TALON's meeting intelligence agent. Return strict JSON with summary, key_topics, action_items, decisions, commitments, coaching_observations, leadership_patterns, emotional_tone, risks_or_blockers, recommended_next_steps, follow_up_email.",
            f"Title: {title}\nTranscript:\n{transcript}\n\nKnowledge context:\n{context or 'None'}",
            fallback,
        )
