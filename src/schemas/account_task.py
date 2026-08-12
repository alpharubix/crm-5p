from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class AccountTaskCreate(BaseModel):
    module_name: str = "Account"
    account_id: str | int
    task_type: str  # Call, Update Record, Email, Move Status
    task_description: Optional[str] = None
    task_assigned_date_time: Optional[datetime] = None
    task_due_date_time: Optional[datetime] = None
    task_status: str = "Unassigned"  # Unassigned, Assigned, Pending, In Progress, Completed, Verified, Overdue
    assigned_to_id: Optional[str | int] = None

class BulkAccountTaskCreate(BaseModel):
    account_ids: List[str | int]
    task_status: Optional[str] = "Unassigned"
    task_assigned_date_time: Optional[datetime] = None
    task_due_date_time: Optional[datetime] = None
    task_description: Optional[str] = None

class BulkTaskStatusUpdate(BaseModel):
    task_ids: List[str | int]
    task_status: str

class AccountTaskUpdate(BaseModel):
    task_type: Optional[str] = None
    task_description: Optional[str] = None
    task_assigned_date_time: Optional[datetime] = None
    task_due_date_time: Optional[datetime] = None
    task_status: Optional[str] = None
    assigned_to_id: Optional[str | int] = None
    account_id: Optional[str | int] = None

class AccountTaskSchema(BaseModel):
    id: str | int
    module_name: str
    account_id: str | int
    account_name: Optional[str] = None
    account_owner: Optional[str] = None
    account_owner_id: Optional[str | int] = None
    account_status: Optional[str] = None
    account_stage: Optional[str] = None
    call_back_date_status: Optional[str] = None
    task_type: str
    task_description: Optional[str] = None
    task_assigned_date_time: Optional[datetime] = None
    task_due_date_time: Optional[datetime] = None
    task_status: str
    assigned_to_id: Optional[str | int] = None
    assigned_to_name: Optional[str] = None
    created_by_id: Optional[str | int] = None
    modified_by_id: Optional[str | int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AccountTaskListResponse(BaseModel):
    data: List[AccountTaskSchema]
    page_info: dict
