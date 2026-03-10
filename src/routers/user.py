from urllib import request

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from ..controllers.user import insert_already_existing_user,get_user_filter,get_all_users
from ..database import get_db
from ..schemas.user import ExistingUser, UserFilterResponse,UserResponseList
router = APIRouter(prefix="/user")


@router.post("/create-user")
async def create_user(user: ExistingUser, db: Session = Depends(get_db)):
    return insert_already_existing_user(user, db)


@router.get("/filter", response_model=UserFilterResponse)
async def get_user(request: Request, db: Session = Depends(get_db)):
   return get_user_filter(request,db)


@router.get("/mentions",response_model=UserResponseList)
async def get_user_for_mention(db: Session = Depends(get_db)):
    return get_all_users(db)


