from typing import Dict, Any
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from starlette.requests import Request
from src.schemas.deals import GetListDealResponse,DealCreationBody
from src.controllers.deals import get_deals,create_deal,update_deal_based_on_id
from src.database import get_db

deals_router = APIRouter(prefix="/deals", tags=["deals"])


@deals_router.get("",response_model=GetListDealResponse)
@deals_router.get("/",response_model=GetListDealResponse)
def get_deals_list(request:Request,db:Session=Depends(get_db),page: int = 1,deal_id : int | None = None):
    return get_deals(page, db, int(request.state.user_id), request.state.role, deal_id)

@deals_router.post("/", response_model=DealCreationBody)
def create_deal_route_function(deal:DealCreationBody,request:Request,db:Session=Depends(get_db),):
    return create_deal(deal,db,request.state.user_id, request.state.role)

@deals_router.put("/{deal_id}")
async def update_deal(
    request: Request,
    deal_id: int,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    return update_deal_based_on_id(user_id=request.state.user_id,user_role=request.state.role,deal_id=deal_id,payload=payload,db=db)

