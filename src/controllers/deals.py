import math

from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.models.deal import Deal

def get_deals(page,db:Session, user_id:int):
    try:
        limit = 30
        offset = (page - 1) * limit
        total_records = db.query(Deal).filter(Deal.deal_owner_id == user_id).count()
        deals = db.query(Deal).filter(Deal.deal_owner_id == user_id).offset(offset).limit(limit).all()
        total_pages = math.ceil(total_records / limit)
        return {"data":deals,"page_info":{
            "total_pages":total_pages,
            "page":page,
            "data_size":limit,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message":"Internal Server Error"})

