import math

from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.models.deal import Deal
from src.controllers.auth import MANAGERID

def get_deals(page, db: Session, user_id: int, user_role: str, deal_id: int | None = None):
    try:
        limit = 30
        offset = (page - 1) * limit
        MANAGER_EXECUTIVES_MAP = MANAGERID.MANAGER_EXECUTIVES_MAP  # class-level access
        allowed_owner_ids = None  # not [None]
        filters = []

        if user_role in ("super_admin", "admin"):
            pass
        elif user_role == "manager":
            allowed_owner_ids = [user_id] + MANAGER_EXECUTIVES_MAP.get(user_id, [])
        elif user_role == "executive":
            allowed_owner_ids = [user_id]

        if allowed_owner_ids is not None:
            filters.append(Deal.deal_owner_id.in_(allowed_owner_ids))
        if deal_id:
            filters.append(Deal.id == deal_id)

        total_records = db.query(Deal).filter(*filters).count()
        deals = db.query(Deal).filter(*filters).offset(offset).limit(limit).all()
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

        return {
            "data": deals,
            "page_info": {
                "total_pages": total_pages,
                "page": page,
                "data_size": total_records,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal Server Error"})
