from fastapi import APIRouter, Depends
from pymongo.synchronous.collection import Collection
from sqlalchemy.orm import Session
from starlette.requests import Request

from src.controllers.notes import insert_notes
from src.database import get_db, get_mongodb
from src.schemas.note import Note

notes_router = APIRouter(prefix="/notes")

@notes_router.post("")
@notes_router.post("/")
def create_notes(
    request: Request,
    body: Note,
    collection: Collection = Depends(get_mongodb),
    pg_db_session: Session = Depends(get_db),
):
    return insert_notes(
        module_name=body.module,
        user_id=request.state.user_id,
        note=body.note,
        user_role=request.state.role,
        parent_id=body.id,
        db=collection,
        pg_db=pg_db_session,
    )
