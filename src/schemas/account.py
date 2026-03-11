from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_serializer,
    field_validator,
)

from src.schemas.contact import ContactResponse
from src.schemas.user import UserResponseAccount
from src.schemas.deals import DealSchema

# Account Status Options
AccountStatusType = Literal[
    "Awareness",
    "Attention",
    "Assessment",
    "Lender Review",
    "Not Interested",
    "Location Unserviceable",
]

# Account Stage Options
AccountStageType = Literal[
    "Initial Pitch",
    "Product Offering",
    "Doc List Shared to Cust",
    "Partial Docs Rec",
    "Yet To Review",
    "Under Internal Review",
    "In Review with Lender",
    "Interested",
    "Commercial NI",
    "Location not doable",
    "No Requirement",
]


class AccountBase(BaseModel):
    id: str
    # Identity & Contact (Required)
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: str = Field(..., min_length=10, max_length=15)
    account_name: str
    # Workflow & Assignment (Optional)
    account_owner_id: Optional[str] = None
    account_status: Any
    account_stage: Any
    source: Optional[str] = None
    business_status: Optional[str] = None
    distributor_code: Optional[str] = None

    # Business Details (Optional)
    type_of_business: Optional[str] = None
    industry: Optional[str] = None

    # Location (Optional)
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

    # Flags & Dates (Optional)
    waba_interested: Optional[bool] = False
    call_back_date_time: Optional[datetime] = None

    # Custom Fields (JSONB)
    custom_fields: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_by_id: str
    created_time: str | datetime
    modified_time: str | datetime

    @field_validator("created_time", mode="after")
    @classmethod
    def parse_created_time(cls, value):
        if isinstance(value, str):
            date = datetime.fromisoformat(value)
            return datetime.fromisoformat(value)
        raise ValueError("created_time must be in string format")

    @field_validator("modified_time", mode="after")
    @classmethod
    def parse_modified_time(cls, value):
        if isinstance(value, str):
            dt = datetime.fromisoformat(value)
            return dt
        raise ValueError("modified_time must be in string format")

    @field_validator("created_by_id", mode="after")
    @classmethod
    def parse_created_by(cls, value):
        if isinstance(value, str):
            return int(value)
        raise ValueError("id must be in string format")

    @field_validator("id", mode="after")
    @classmethod
    def parse_id(cls, value):
        if isinstance(value, str):
            return int(value)
        raise ValueError("id must be in string format")


from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime


class AccountResponse(BaseModel):

    id: Optional[str] = None
    first_name: Optional[Any] = None
    last_name: Optional[Any] = None
    account_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    business_status: Optional[str] = None
    distributor_code: Optional[str] = None
    call_back_date_time: Optional[datetime] = None
    type_of_business: Optional[str] = None
    industry: Optional[str] = None
    account_status: Optional[Any] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    source: Optional[str] = None
    account_stage: Optional[Any] = None

    created_by_id: Optional[str] = None
    created_time: Optional[datetime] = None
    modified_time: Optional[datetime] = None

    created_by: Optional[UserResponseAccount] = None
    owner:  Optional[UserResponseAccount] = None
    account_linked_contact: Optional[List["ContactResponse"]] = None
    deals: Optional[List["DealSchema"]] = None

    notes: Optional[Any] = None
    custom_fields: Optional[Dict[str, Any]] = None

    model_config = {
        "from_attributes": True
    }

    @field_validator("id", "created_by_id", mode="before")
    @classmethod
    def coerce_ids_to_str(cls, value):
        return str(value) if value is not None else None

class GetlistAccountResponse(BaseModel):
    data: List[AccountResponse] = []
    page_info: dict[str, Any]


class GetAssociatedAccountResponse(BaseModel):
    id: int
    account_name: str | Any
    phone: str | Any = None
    email: Optional[str] = None

    @field_serializer("id")
    @classmethod
    def parse_id(cls, value):
        if isinstance(value, int):
            return str(value)
        else:
            return value

class AccountItem(BaseModel):
    id: int | str
    account_name: Any

    @field_serializer("id")
    def serialize_id(self, value):
        return str(value)

class ListAccountsResponse(BaseModel):
    data: List[AccountItem]