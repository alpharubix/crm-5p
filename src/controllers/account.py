import logging
import math
from datetime import datetime
from typing import Optional
import io
import pandas as pd
from fastapi import HTTPException, UploadFile
from pymongo.synchronous.collection import Collection
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload, selectinload
from starlette.requests import Request
from starlette.responses import JSONResponse
from src.controllers.auth import MANAGERID
from src.controllers.notes import get_notes
from src.utility.utils import get_account_headers

from ..models.account import Account
from ..schemas.account import AccountBase, ListAccountsResponse


def create_account(db: Session, data: AccountBase, created_by: str = "") -> Account:
    if db.query(Account).filter(Account.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email exists")

    new_account = Account(
        id=data.id,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        account_name=data.account_name,
        account_owner_id=data.account_owner_id,
        account_status=data.account_status,
        account_stage=data.account_stage,
        source=data.source,
        business_status=data.business_status,
        distributor_code=data.distributor_code,
        type_of_business=data.type_of_business,
        industry=data.industry,
        city=data.city,
        state=data.state,
        pincode=data.pincode,
        waba_interested=data.waba_interested,
        call_back_date_time=data.call_back_date_time,
        custom_fields=data.custom_fields,
        created_by_id=data.created_by_id,
        created_time=data.created_time,
        modified_time=data.modified_time,
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account


def get_all_accounts(
    request: Request,
    db: Session,
    mongodb: Collection,
    page: int,
    account_name: Optional[str] = None,
    account_id: Optional[int] = None,
    account_status: Optional[str] = None,
    account_stage: Optional[str] = None,
    source: Optional[str] = None,
    type_of_business: Optional[str] = None,
    industry: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    pincode: Optional[str] = None,
    waba_interested: Optional[bool] = None,
    business_status: Optional[str] = None,
    call_back_date_time: Optional[datetime] = None,
    account_owner_id: Optional[int] = None,
    phone_number: Optional[str] = None,
):
    MANAGER_EXECUTIVES_MAP = (
        MANAGERID().MANAGER_EXECUTIVES_MAP
    )  # manager is mapping object

    limit = 30
    offset = (page - 1) * limit
    query = db.query(Account)
    filters = []
    user_id = request.state.user_id
    role = request.state.role

    allowed_owner_ids = None

    if role in ("super_admin", "admin"):
        pass  # no restriction

    elif role == "manager":
        allowed_owner_ids = [user_id] + MANAGER_EXECUTIVES_MAP.get(user_id, [])

    elif role == "executive":
        allowed_owner_ids = [user_id]

    # filters.append(Account.account_owner_id == request.state.user_id)
    if allowed_owner_ids is not None:
        filters.append(Account.account_owner_id.in_(allowed_owner_ids))

    if account_id is not None:
        filters.append(Account.id == account_id)
    if account_name:
        filters.append(Account.account_name.ilike(f"%{account_name.strip()}%"))
    if account_status:
        filters.append(Account.account_status.ilike(f"{account_status.strip()}%"))
    if account_stage:
        filters.append(Account.account_stage.ilike(f"{account_stage.strip()}%"))
    if source:
        filters.append(Account.source.ilike(f"{source.strip()}%"))
    if type_of_business:
        filters.append(Account.type_of_business == type_of_business)
    if industry:
        filters.append(Account.industry == industry)
    if city:
        filters.append(Account.city.ilike(f"%{city.strip()}%"))
    if state:
        filters.append(Account.state.ilike(f"%{state.strip()}%"))
    if pincode:
        filters.append(Account.pincode == pincode)
    if waba_interested is not None:
        filters.append(Account.waba_interested == waba_interested)
    if business_status:
        filters.append(Account.business_status == business_status)
    if call_back_date_time:
        filters.append(Account.call_back_date_time != None)  # excludes NULLs explicitly
        filters.append(Account.call_back_date_time <= call_back_date_time)
    if phone_number and phone_number.strip():
        filters.append(
            or_(
                Account.phone.like(f"%{phone_number}%"),
                Account.phone.like(f"%91{phone_number}%"),
                Account.phone.like(f"%+91{phone_number}%")
            )
        )
    if account_owner_id:

        if role in ('super_admin', 'admin'):
            filters.append(Account.account_owner_id==int(account_owner_id))
        elif user_id not in MANAGER_EXECUTIVES_MAP:
            raise HTTPException(
                status_code=403,
                detail={
                    "message": "You do not have permission to access records for this account owner",
                    "success": False,
                },
            )
        elif account_owner_id in MANAGER_EXECUTIVES_MAP.get(user_id):
            filters.append(Account.account_owner_id == int(account_owner_id))
        else:
            raise HTTPException(
                status_code=403,
                detail={
                    "message": "You do not have permission to access records for this account owner",
                    "success": False,

                },
            )
    print(filters)
    base_query = query.filter(and_(*filters)) if filters else query
    total_data_size = base_query.count()
    data = (
        base_query.offset(offset)  # query performance optimization
        .options(
            selectinload(Account.owner),
            selectinload(Account.created_by),
            selectinload(Account.account_linked_contact),
        )
        .limit(limit)
        .all()
    )
    if len(data) != 0:
        account_ids = [acc.id for acc in data]
        accounts_notes = get_notes(acc_ids=account_ids, notes_collection=mongodb['Notes'])

        for acc in data:
            acc.notes = accounts_notes.get(str(acc.id))
    total_pages = math.ceil(total_data_size / limit)

    return {
        "data": data,  # Return the clean dictionaries
        "page_info": {
            "page": page,
            "total_pages": total_pages,
            "data_size": total_data_size,
        },
    }


def update_account(
    db: Session, account_id: int, data: AccountBase, modified_by: str = ""
) -> Account:
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account_data = data.model_dump(exclude_unset=True)
    for key, value in account_data.items():
        setattr(account, key, value)

    account.modified_by = modified_by  # type: ignore

    db.commit()
    db.refresh(account)
    return account


def get_account_by_id(db: Session, account_id: int) -> Account:
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


async def accounts_csv_update(file:UploadFile,db:Session):
    try:
        if file.filename.endswith(".csv"):
            #if the file is csv file process the file
            contents = await file.read()
            csv_data = io.BytesIO(contents)
            df = pd.read_csv(csv_data)
            data = df.to_dict(orient="records")
            if len(data) == 0:
                return JSONResponse(status_code=400,content={"message": "At least 1 row is required"})
            #after getting the data check the headers
            required_headers = {"id","account_owner_id"}
            csv_headers = set(data[0].keys())
            if required_headers != csv_headers:
                return JSONResponse(status_code=400,content={"message": "Excel headers mismatch found"})
            db.bulk_update_mappings(Account,data)
            db.commit()
            return JSONResponse(status_code=200, content={"message": f"{len(data)} accounts updated successfully"})
        else:
            return JSONResponse(status_code=422, content="Only csv files are supported")
    except Exception as e:
        print(e)
        db.rollback()
        logging.exception("CSV account update failed")
        raise HTTPException(
            status_code=500,
            detail={"message": "Error processing CSV file"}
        )

def fetch_account_id(account_name:str,db:Session):
    try:
        results = (
            db.query(
                Account.id.label("id"),
                Account.account_name.label("account_name")
            )
            .filter(Account.account_name.ilike(f"%{account_name.strip()}%"))
            .limit(10)
            .all()
        )
        print(results)
        if len(results) == 0:
            return JSONResponse(status_code=404, content={"data":[]})
        # Convert to list of dicts
        dict_results = [row._asdict() for row in results]
        print(dict_results)
        return {"data":dict_results}
    except Exception as e:
        logging.exception(e)
        raise HTTPException(status_code=500, detail={"message":"Internal server error"})

# async def update_accounts_based_on_csv(file, db: Session):
#     try:
#         if not file.filename.endswith(".csv"):
#             raise HTTPException(status_code=400, detail={"message": "only support csv file"})
#         else:
#             contents = await file.read()
#             csv_data = io.BytesIO(contents)
#             df = pd.read_csv(csv_data)
#             if df.empty:
#                 raise HTTPException(status_code=400, detail="Csv file is empty")
#             else:
#                 data = df.to_dict(orient="records")
#                 account_headers = get_account_headers()











