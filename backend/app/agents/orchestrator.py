from sqlalchemy.orm import Session

from app.agents.coach_agent import CoachAgent
from app.agents.content_agent import ContentAgent
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.meeting_agent import MeetingAgent
from app.services.ai_service import AIService


class OrchestratorAgent:
    def __init__(self) -> None:
        ai = AIService()
        self.knowledge = KnowledgeAgent()
        self.coach = CoachAgent(ai)
        self.meeting = MeetingAgent(ai)
        self.content = ContentAgent(ai)

    def coach_analysis(self, db: Session, prompt: str, context: str | None = None) -> dict:
        knowledge = self.knowledge.retrieve_context(db, prompt)
        return self.coach.analyze(prompt, "\n\n".join(filter(None, [context, knowledge])))

    def meeting_analysis(self, db: Session, title: str, transcript: str) -> dict:
        knowledge = self.knowledge.retrieve_context(db, transcript)
        return self.meeting.analyze(title, transcript, knowledge)

    def content_generation(self, db: Session, content_type: str, topic: str, tone: str, context: str | None = None) -> dict:
        knowledge = self.knowledge.retrieve_context(db, topic)
        return self.content.generate(content_type, topic, tone, "\n\n".join(filter(None, [context, knowledge])))

