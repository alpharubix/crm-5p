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
        for deal in deals:

                if deal.id:
                    deal.id = str(deal.id)

                if deal.deal_owner_id:
                    deal.deal_owner_id = str(deal.deal_owner_id)

                if deal.assignee_id:
                    deal.assignee_id = str(deal.assignee_id)

                if deal.account_id:
                    deal.account_id = str(deal.account_id)

                if deal.created_by:
                    deal.created_by = str(deal.created_by)

                if deal.modified_by:
                    deal.modified_by = str(deal.modified_by)
        total_pages = math.ceil(total_records / limit)
        return {"data":deals,"page_info":{
            "total_pages":total_pages,
            "page":page,
            "data_size":limit,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message":"Internal Server Error"})

