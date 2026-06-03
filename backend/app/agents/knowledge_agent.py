from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models


class KnowledgeAgent:
    name = "KnowledgeAgent"

    def retrieve_context(self, db: Session, query: str, limit: int = 3) -> str:
        terms = [term.lower() for term in query.split() if len(term) > 3]
        docs = db.scalars(select(models.KnowledgeDocument).order_by(models.KnowledgeDocument.created_at.desc())).all()
        scored = []
        for doc in docs:
            haystack = f"{doc.title} {doc.category or ''} {doc.content} {' '.join(doc.tags or [])}".lower()
            score = sum(1 for term in terms if term in haystack)
            if score:
                scored.append((score, doc))
        chosen = [doc for _, doc in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]]
        if not chosen:
            chosen = docs[:limit]
        return "\n\n".join(f"{doc.title}: {doc.content[:900]}" for doc in chosen)

