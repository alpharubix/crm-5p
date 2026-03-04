from urllib import request

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.requests import Request

from src.controllers.deals import get_deals
from src.database import get_db

deals_router = APIRouter()


@deals_router.get("/deals")
def get_deals_list(request:Request,db:Session=Depends(get_db),page: int = 1):
    return get_deals(page,db,request.state.user_id)
