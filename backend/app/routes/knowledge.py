from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import knowledge_repository
from app.schemas.knowledge_schema import KnowledgeCreate, KnowledgeRead

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("", response_model=list[KnowledgeRead])
def get_knowledge(db: Session = Depends(get_db)):
    return knowledge_repository.list_knowledge(db)


@router.post("", response_model=KnowledgeRead, status_code=status.HTTP_201_CREATED)
def create_knowledge(payload: KnowledgeCreate, db: Session = Depends(get_db)):
    return knowledge_repository.create_knowledge(db, payload)


@router.delete("/{knowledge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge(knowledge_id: UUID, db: Session = Depends(get_db)):
    if not knowledge_repository.delete_knowledge(db, knowledge_id):
        raise HTTPException(status_code=404, detail="Knowledge document not found")

