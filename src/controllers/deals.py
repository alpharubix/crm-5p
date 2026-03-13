import math
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session,selectinload

from src.schemas.deals import DealCreationBody, IST
from src.controllers.audit_log import log_action
from src.models.deal import Deal
from src.controllers.auth import MANAGERID

def get_deals(
    page,
    db: Session,
    user_id: int,
    user_role: str,
    deal_id: int | None = None,
    account_name: str | None = None,
    lender_name: str | None = None,
    case_status: str | None = None,
    ticket_login: str | None = None,
    loan_type: str | None = None,
    type_of_case_login: str | None = None,
    deal_owner_id: int | None = None,
):
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

        if account_name:
            filters.append(Deal.account_name.ilike(f"%{account_name.strip()}%"))

        if lender_name:
            filters.append(Deal.lender_name.ilike(f"%{lender_name.strip()}%"))

        if case_status:
            filters.append(Deal.case_status.ilike(f"{case_status.strip()}%"))

        if ticket_login:
            filters.append(Deal.ticket_login.ilike(f"{ticket_login.strip()}%"))

        if loan_type:
            filters.append(Deal.loan_type.ilike(f"{loan_type.strip()}%"))

        if type_of_case_login:
            filters.append(Deal.type_of_case_login.like(f"{type_of_case_login.strip()}%"))

        if deal_owner_id:
            filters.append(Deal.deal_owner_id == deal_owner_id)

        total_records = db.query(Deal).filter(*filters).count()
        deals = db.query(Deal).filter(*filters).options(selectinload(Deal.owner)).offset(offset).limit(limit).all()
        for deal in deals:
            deal.payment_receipt = None
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
        print(e)
        raise HTTPException(status_code=500, detail={"message": "Internal Server Error"})

def create_deal(deal:DealCreationBody,db:Session,user_id,user_role):
    try:
        created_deal  = Deal(
    account_id=deal.account_id,
    ticket_id=deal.ticket_id,
    ticket_number=deal.ticket_number,
    deal_type=deal.deal_type,
    loan_type=deal.loan_type,
    type_of_login=deal.type_of_login,
    type_of_case_login=deal.type_of_case_login,
    ticket_login=deal.ticket_login,
    case_stage=deal.case_stage,
    case_status=deal.case_status,
    disbursed_amount=deal.disbursed_amount,
    sanction_amount=deal.sanction_amount,
    approved_amount=deal.approved_amount,
    amount_required=deal.amount_required,
    processing_fees=deal.processing_fees,
    mm_charges=deal.mm_charges,
    insurance_amount=deal.insurance_amount,
    pf_percentage=deal.pf_percentage,
    rate_of_interest=deal.rate_of_interest,
    interest_type=deal.interest_type,
    deal_call_back_datetime=deal.deal_call_back_datetime,
    disbursement_date=deal.disbursement_date,
    lender_login_date=deal.lender_login_date,
    loan_start_date=deal.loan_start_date,
    loan_end_date=deal.loan_end_date,
    targeted_disbursement_date=deal.targeted_disbursement_date,
    tenure=deal.tenure,
    lender_code=deal.lender_code,
    lender_name=deal.lender_name,
    customer_rejection_reason=deal.customer_rejection_reason,
    customer_rejection_status_explanation=deal.customer_rejection_status_explanation,
    lender_rejection_reason=deal.lender_rejection_reason,
    lender_rejection_status_explanation=deal.lender_rejection_status_explanation,
    payment_receipt=deal.payment_receipt,
    sanction_letter=deal.sanction_letter,
    potential=deal.potential,
    product=deal.product,
    assignee_id=deal.assignee_id,
    created_by=user_id,
    modified_by=deal.modified_by,
    account_name=deal.account_name,
    deal_owner_id=user_id,
    crm_deal_id=deal.crm_deal_id,
)
        db.add(created_deal)
        db.commit()
        db.refresh(created_deal)

        log_action(
            db, user_id, user_role, "CREATED", "DEAL", created_deal.id, deal.model_dump()
        )
        return created_deal

    except Exception as e:
        print("Error happened on deal creation time",e)
        db.rollback()
        raise HTTPException(status_code=500, detail={"message": "Internal Server Error"})


def update_deal_based_on_id(user_id,user_role,db:Session,deal_id:int,payload):

    db_deal : Deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not db_deal:
        raise HTTPException(status_code=404, detail={"msg": "Deal not found"})

    for key, value in payload.items():
        if hasattr(db_deal, key):
            if value == "" or value is None:
                setattr(db_deal, key, None)
            elif "datetime" in key or "date" in key:
                if isinstance(value, str):
                    try:
                        parsed = datetime.fromisoformat(value)
                        if parsed.tzinfo is None:
                            parsed = parsed.replace(tzinfo=IST)
                        setattr(db_deal, key, parsed)
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail={"msg": f"Invalid date format for field: {key}"},
                        )
                else:
                    setattr(db_deal, key, value)
            else:
                setattr(db_deal, key, value)

    db_deal.modified_by = user_id
    db_deal.updated_at = datetime.now(IST)

    try:
        db.commit()
        db.refresh(db_deal)
        log_action(db, user_id, user_role, "UPDATED", "Deals", deal_id, payload)
        return {"message": "update-success", "updated_deal_id": str(db_deal.id)}
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")




