import math
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_
from sqlalchemy.orm import Session, selectinload

from src.controllers.audit_log import log_action
from src.models.deal import Deal
from src.models.ticket import Ticket
from src.controllers.auth import MANAGERID
from src.controllers.notes import get_notes


def get_deals(
    page,
    db: Session,
    mongodb_conn,
    user_id: int,
    user_role: str,
    deal_id: int | None = None,
    account_name: str | None = None,
    case_status: str | None = None,
    loan_type: str | None = None,
    deal_owner_id: int | None = None,
    kanban: bool = False,
    created_from: str | None = None,
    created_to: str | None = None,
):
    from src.models.ticket import Ticket  # Explicit import to prevent relationship lookup failure

    MANAGER_EXECUTIVES_MAP = MANAGERID.MANAGER_EXECUTIVES_MAP
    page = page or 1
    limit = 30
    offset = (page - 1) * limit
    filters = []
    allowed_owner_ids = None

    if user_role == "manager":
        allowed_owner_ids = [user_id] + MANAGER_EXECUTIVES_MAP.get(user_id, [])
    elif user_role == "executive":
        allowed_owner_ids = [user_id]

    if allowed_owner_ids is not None:
        filters.append(Deal.deal_owner_id.in_(allowed_owner_ids))

    if deal_id:
        filters.append(Deal.id == deal_id)
    if account_name:
        filters.append(Deal.account_name.ilike(f"%{account_name.strip()}%"))
    if case_status:
        filters.append(Deal.case_status.ilike(f"%{case_status.strip()}%"))
    if loan_type:
        filters.append(Deal.loan_type.ilike(f"%{loan_type.strip()}%"))
    if deal_owner_id:
        filters.append(Deal.deal_owner_id == deal_owner_id)

    if kanban:
        date_from = (
            datetime.strptime(created_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if created_from
            else datetime.now(timezone.utc) - timedelta(days=30)
        )
        date_to = (
            datetime.strptime(created_to, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if created_to
            else datetime.now(timezone.utc)
        )
        filters.append(Deal.created_at >= date_from)
        filters.append(Deal.created_at <= date_to)

        base_query = db.query(Deal).filter(and_(*filters))
        deals = (
            base_query
            .with_entities(
                Deal.id,
                Deal.account_name,
                Deal.lender_name,
                Deal.case_status,
                Deal.loan_type,
                Deal.deal_owner_id,
            )
            .all()
        )
        grouped: dict = {}
        for deal in deals:
            status = deal.case_status or "No Status"
            grouped.setdefault(status, []).append({
                **deal._asdict(),
                "id": str(deal.id),
                "deal_owner_id": str(deal.deal_owner_id) if deal.deal_owner_id else None,
            })

        return {"data": grouped, "page_info": None}

    base_query = db.query(Deal).filter(and_(*filters))

    if deal_id:
        deals = (
            base_query
            .options(selectinload(Deal.owner))
            .limit(1)
            .all()
        )
        if deals:
            deal = deals[0]

            ids_list = [str(deal.id)]
            if getattr(deal, "crm_deal_id", None):
                ids_list.append(str(deal.crm_deal_id))
            
            # explicitly query tickets based on Deal ID to bypass relationship mapping issues
            tickets_records = db.query(Ticket).filter(Ticket.deal_id == deal.id).all()
            
            serialized_tickets = []
            for ticket in tickets_records:
                ids_list.append(str(ticket.id))
                t_dict = {c.name: getattr(ticket, c.name) for c in ticket.__table__.columns}
                
                # Stringify IDs to match schema
                for key in ("id", "deal_id", "created_by", "modified_by", "partner_code"):
                    if t_dict.get(key) is not None:
                        t_dict[key] = str(t_dict[key])
                serialized_tickets.append(t_dict)

            # fetch notes matching either Deal or Tickets modules
            notes = get_notes(
                id_list=ids_list,
                notes_collection=mongodb_conn["Notes"],
                module_name=["Deals", "Tickets"]
            )

            # Manually construct the final Deal dictionary to ensure injection works
            deal_dict = {c.name: getattr(deal, c.name) for c in deal.__table__.columns}
            deal_dict["id"] = str(deal.id)
            if deal.deal_owner_id:
                deal_dict["deal_owner_id"] = str(deal.deal_owner_id)
            if deal.account_id:
                deal_dict["account_id"] = str(deal.account_id)
                
            deal_dict["payment_receipt"] = None
            deal_dict["notes"] = notes
            deal_dict["tickets"] = serialized_tickets  # Array of fully serialized tickets

            if getattr(deal, "owner", None):
                deal_dict["owner"] = {
                    "id": str(deal.owner.id),
                    "full_name": getattr(deal.owner, "full_name", ""),
                    "email": getattr(deal.owner, "email", "")
                }

            return {
                "data": [deal_dict],
                "page_info": {"page": 1, "total_pages": 1, "data_size": 1},
            }

        return {
            "data": [],
            "page_info": {"page": 1, "total_pages": 0, "data_size": 0},
        }
    
    total_records = base_query.count()
    deals = (
        base_query
        .with_entities(
            Deal.id,
            Deal.account_name,
            Deal.lender_name,
            Deal.case_status,
            Deal.loan_type,
            Deal.ticket_login,
            Deal.deal_owner_id,
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    total_pages = math.ceil(total_records / limit)

    return {
        "data": [
            {
                **d._asdict(),
                "id": str(d.id),
                "deal_owner_id": str(d.deal_owner_id) if d.deal_owner_id else None,
            }
            for d in deals
        ],
        "page_info": {"page": page, "total_pages": total_pages, "data_size": total_records},
    }


def create_deal(deal, db: Session, user_id, user_role):
    try:
        created_deal = Deal(
            account_id=deal.account_id,
            account_name=deal.account_name,
            deal_type=deal.deal_type,
            loan_type=deal.loan_type,
            type_of_login=deal.type_of_login,
            type_of_case_login=deal.type_of_case_login,
            ticket_login=deal.ticket_login,
            case_stage=deal.case_stage,
            case_status=deal.case_status,
            amount_required=deal.amount_required,
            mm_charges=deal.mm_charges,
            lender_name=deal.lender_name,
            lender_code=deal.lender_code,
            deal_call_back_datetime=deal.deal_call_back_datetime,
            customer_rejection_reason=deal.customer_rejection_reason,
            customer_rejection_status_explanation=deal.customer_rejection_status_explanation,
            deal_owner_id=user_id,
            created_by=user_id,
            modified_by=user_id,
        )
        db.add(created_deal)
        db.commit()
        db.refresh(created_deal)
        safe_payload = jsonable_encoder(deal)
        
        log_action(db, user_id, user_role, "CREATED", "DEAL", created_deal.id, safe_payload)
        
        return created_deal
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"message": str(e)})

def update_deal_based_on_id(user_id, user_role, db: Session, deal_id: int, payload):
    db_deal = db.query(Deal).filter(Deal.id == deal_id).first()
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
    db_deal.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(db_deal)
        log_action(db, user_id, user_role, "UPDATED", "Deals", deal_id, payload)
        return {"message": "update-success", "updated_deal_id": str(db_deal.id)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")