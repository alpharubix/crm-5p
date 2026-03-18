import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from starlette.requests import Request

from ..models.account import Account
from ..controllers.auth import MANAGERID


def export_accounts_csv(
    request: Request,
    db: Session,
    account_name: Optional[str] = None,
    account_status: Optional[str] = None,
    account_stage: Optional[str] = None,
    source: Optional[str] = None,
    industry: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    phone_number: Optional[str] = None,
    account_owner_id: Optional[int] = None,
    call_back_date_time: Optional[str] = None,
):
    

    # --- . RBAC ---
    MANAGER_EXECUTIVES_MAP = MANAGERID().MANAGER_EXECUTIVES_MAP
    user_id = request.state.user_id
    role = request.state.role

    filters = []

    if role in ("super_admin", "admin"):
        pass
    elif role == "manager":
        allowed_owner_ids = [user_id] + MANAGER_EXECUTIVES_MAP.get(user_id, [])
        filters.append(Account.account_owner_id.in_(allowed_owner_ids))
    elif role == "executive":
        filters.append(Account.account_owner_id == user_id)

    # --- . Block bulk export FIRST, before anything else ---
    no_filters_applied = not any([
        account_name,
        account_status,
        account_stage,
        source,
        industry,
        city,
        state,
        phone_number,
        account_owner_id,
        call_back_date_time,
    ])

    if no_filters_applied:
        raise HTTPException(
            status_code=403,
            detail="Bulk export is not available yet. Please apply at least one filter."
        )

    # --- . Query filters ---
    if account_name:
        filters.append(Account.account_name.ilike(f"%{account_name.strip()}%"))
    if account_status:
        filters.append(Account.account_status.ilike(f"{account_status.strip()}%"))
    if account_stage:
        filters.append(Account.account_stage.ilike(f"{account_stage.strip()}%"))
    if source:
        filters.append(Account.source.ilike(f"{source.strip()}%"))
    if industry:
        filters.append(Account.industry == industry)
    if city:
        filters.append(Account.city.ilike(f"%{city.strip()}%"))
    if state:
        filters.append(Account.state.ilike(f"%{state.strip()}%"))
    if phone_number and phone_number.strip():
        filters.append(
            or_(
                Account.phone.like(f"%{phone_number}%"),
                Account.phone.like(f"%91{phone_number}%"),
                Account.phone.like(f"%+91{phone_number}%"),
            )
        )
    if account_owner_id:
        if role in ("super_admin", "admin"):
            filters.append(Account.account_owner_id == int(account_owner_id))
        elif user_id not in MANAGER_EXECUTIVES_MAP:
            raise HTTPException(status_code=403, detail="No permission for this owner")
        elif account_owner_id in MANAGER_EXECUTIVES_MAP.get(user_id, []):
            filters.append(Account.account_owner_id == int(account_owner_id))
        else:
            raise HTTPException(status_code=403, detail="No permission for this owner")
    if call_back_date_time:
        try:
            dt = datetime.fromisoformat(call_back_date_time)
            filters.append(Account.call_back_date_time != None)
            filters.append(Account.call_back_date_time <= dt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid call_back_date_time format. Use ISO format e.g. 2024-01-31T00:00:00"
            )

    # --- . Fetch rows ---
    rows = (
        db.query(
            Account.id,
            Account.account_name,
            Account.phone,
            Account.account_status,
            Account.account_stage,
            Account.source,
            Account.type_of_business,
            Account.industry,
            Account.city,
            Account.state,
            Account.pincode,
            Account.business_status,
            Account.distributor_code,
            Account.waba_interested,
            Account.call_back_date_time,
            Account.created_time,
            Account.account_owner_id,
        )
        .filter(and_(*filters) if filters else True)
        .all()
    )

    # --- . Stream CSV ---
    def generate():
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "ID", "Account Name", "Phone", "Account Status", "Account Stage",
            "Source", "Type of Business", "Industry", "City", "State",
            "Pincode", "Business Status", "Distributor Code", "WABA Interested",
            "Callback DateTime", "Created Time", "Account Owner ID",
        ])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        for row in rows:
            writer.writerow([
                str(row.id) if row.id else "",
                row.account_name or "",
                row.phone or "",
                row.account_status or "",
                row.account_stage or "",
                row.source or "",
                row.type_of_business or "",
                row.industry or "",
                row.city or "",
                row.state or "",
                row.pincode or "",
                row.business_status or "",
                row.distributor_code or "",
                str(row.waba_interested) if row.waba_interested is not None else "",
                row.call_back_date_time.strftime("%Y-%m-%d %H:%M:%S") if row.call_back_date_time else "",
                row.created_time.strftime("%Y-%m-%d %H:%M:%S") if row.created_time else "",
                str(row.account_owner_id) if row.account_owner_id else "",
            ])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    filename = f"accounts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )



