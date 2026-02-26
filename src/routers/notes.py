from fastapi import APIRouter, Depends, HTTPException
from pymongo.synchronous.collection import Collection
from sqlalchemy.orm import sessionmaker, Session
from starlette.requests import Request
from src.database import get_mongodb, get_db
from src.controllers.notes import insert_notes
from src.schemas.note import Note
notes_router = APIRouter(prefix='/notes')


@notes_router.post('')
@notes_router.post('/')
def create_notes( request:Request,body:Note,collection: Collection = Depends(get_mongodb),pg_db_session:Session = Depends(get_db)):
    return insert_notes(user_id=request.state.user_id, note=body.note,module_name=body.module,parent_id=body.id,db=collection,pg_db=pg_db_session)












