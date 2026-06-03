from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import client_repository
from app.schemas.client_schema import ClientCreate, ClientRead, ClientUpdate

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientRead])
def get_clients(db: Session = Depends(get_db)):
    return client_repository.list_clients(db)


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    return client_repository.create_client(db, payload)


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: UUID, db: Session = Depends(get_db)):
    client = client_repository.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.put("/{client_id}", response_model=ClientRead)
def update_client(client_id: UUID, payload: ClientUpdate, db: Session = Depends(get_db)):
    client = client_repository.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client_repository.update_client(db, client, payload)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: UUID, db: Session = Depends(get_db)):
    client = client_repository.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(client)
    db.commit()

