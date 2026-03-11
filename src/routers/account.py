from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.params import Body
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from starlette.requests import Request

from ..controllers import account as repo
from ..controllers.audit_log import log_action
from ..database import get_db, get_mongodb
from ..models.account import Account
from ..schemas.account import AccountBase, GetlistAccountResponse, ListAccountsResponse

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/")
@router.post("")
def create(request: Request, data: AccountBase, db: Session = Depends(get_db)):
    user_id = int(request.state.user_id)
    user_role = request.state.role
    return repo.create_account(db, data, user_id=user_id, user_role=user_role)


@router.get("/", response_model=GetlistAccountResponse,response_model_exclude_none=True)
@router.get("", response_model=GetlistAccountResponse,response_model_exclude_none=True)
def list_all(
    request: Request,
    account_id: int | None = None,
    city: str | None = None,
    page: int = 1,
    state: str | None = None,
    db: Session = Depends(get_db),
    mongodb=Depends(get_mongodb),
    account_stage: str | None = None,
    account_status: str | None = None,
    account_name: Optional[str] = None,
    account_owner_id: Optional[int] = None,
    industry: str | None = None,
    source: Optional[str] = None,
    phone: str | None = None,
    call_back_date_time: str = None,
):
    return repo.get_all_accounts(
        request=request,
        db=db,
        mongodb=mongodb,
        page=page,
        account_id=account_id,
        city=city,
        state=state,
        account_stage=account_stage,
        account_status=account_status,
        account_name=account_name,
        account_owner_id=account_owner_id,
        source=source,
        phone_number=phone,
        industry=industry,
        call_back_date_time=call_back_date_time,
        # map others only if they exist in repo
    )


@router.put("/{account_id}")
async def update_account(
    request: Request,
    account_id: int,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    user_id = int(request.state.user_id)
    user_role = request.state.role

    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        raise HTTPException(status_code=404, detail={"msg": "Account not found"})

    custom_fields_dict = dict(db_account.custom_fields or {})
    for key, value in payload.items():
        if hasattr(db_account, key):
            if value == "" or value is None:
                setattr(db_account, key, None)
            elif "time" in key or "date" in key:
                if isinstance(value, str):
                    try:
                        value = datetime.fromisoformat(value)
                        if value < datetime.now(timezone.utc):
                            raise HTTPException(
                                status_code=400,
                                detail={"message": "Date should not be in the past"},
                            )
                    except Exception as e:
                        raise e
                    setattr(db_account, key, value)
            else:
                setattr(db_account, key, value)
        else:
            if value == "" or value is None:
                custom_fields_dict[key] = None
            else:
                custom_fields_dict[key] = value

    db_account.custom_fields = custom_fields_dict
    flag_modified(db_account, "custom_fields")
    db_account.modified_by_id = user_id

    try:
        db.commit()
        db.refresh(db_account)
        log_action(db, user_id, user_role, "UPDATED", "Account", account_id, payload)
        return {"message": "update-success", "updated_account": db_account}
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")


@router.post("/accounts-reassignment-csv-upload")
async def upload_accounts_csv(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    # check if the file is in csv format or not
    print("file is under processing")
    response = await repo.accounts_csv_update(file, db)
    return response


@router.get("/lookup", response_model=ListAccountsResponse)
def get_accounts_ids(account_name: str, db: Session = Depends(get_db)):
    return repo.fetch_account_id(account_name, db)


@router.post("/accounts-update-csv-upload")
async def accounts_update_csv(
    request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    try:
        user_id = request.state.user_id
        return await repo.update_accounts_based_on_csv(file, db, user_id)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"unable to process csv error: {str(e)}"
        )


# @router.post("/accounts-update-csv-upload")
# async def accounts_update_csv(file:UploadFile=File(...), db: Session = Depends(get_db)):
#     await repo.update_accounts_based_on_csv(file, db)
#     return {"message":"file upload success"}
