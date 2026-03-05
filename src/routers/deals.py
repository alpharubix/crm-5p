from urllib import request

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.requests import Request

from src.controllers.deals import get_deals
from src.database import get_db

deals_router = APIRouter()


@deals_router.get("/deals")
def get_deals_list(request:Request,db:Session=Depends(get_db),page: int = 1,deal_id : int | None = None):
    return get_deals(page, db, int(request.state.user_id), request.state.role, deal_id)
