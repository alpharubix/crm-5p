from pydantic import BaseModel, field_serializer, Field
from typing import Optional, Any
from datetime import datetime, timezone, timedelta, date

from decimal import Decimal
IST = timezone(timedelta(hours=5, minutes=30))

class DealSchema(BaseModel):

    # Primary Key
    id: Optional[int]
    # Relationship
    account_id: Optional[int]

    # Deal & Ticket Info
    ticket_id: Optional[int]
    ticket_number: Optional[int]
    deal_type: Optional[str]
    loan_type: Optional[str]
    type_of_login: Optional[str]
    type_of_case_login: Optional[str]
    ticket_login: Optional[bool]
    case_stage: Optional[str]
    case_status: Optional[str]

    # Amounts
    disbursed_amount: Optional[Decimal]
    sanction_amount: Optional[Decimal]
    approved_amount: Optional[Decimal]
    amount_required: Optional[Decimal]
    processing_fees: Optional[Decimal]
    mm_charges: Optional[Decimal]
    insurance_amount: Optional[Decimal]
    pf_percentage: Optional[Decimal]
    rate_of_interest: Optional[Decimal]
    interest_type: Optional[str]

    # Dates
    deal_call_back_datetime: Optional[date]
    disbursement_date: Optional[date]
    lender_login_date: Optional[date]
    closing_date: Optional[date]
    loan_end_date: Optional[date]
    targeted_disbursement_date: Optional[date]
    tenure: Optional[int]

    # Lender / Rejection
    lender_code: Optional[str]
    lender_name: Optional[str]
    customer_rejection_reason: Optional[str]
    customer_rejection_status_explanation: Optional[str]
    lender_rejection_reason: Optional[str]
    lender_rejection_status_explanation: Optional[str]

    # Attachments
    payment_receipt: Optional[Any]
    sanction_letter: Optional[str]
    potential: Optional[str]
    product: Optional[str]

    # Audit
    assignee_id: Optional[int]
    created_by: Optional[int]
    modified_by: Optional[int]

    # Account
    account_name: Optional[str]

    # Timestamps
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    deal_owner_id: Optional[int]
    crm_deal_id: Optional[int]

    model_config = {
        "from_attributes": True
    }

    # ---- ID Serializers ----

    @field_serializer(
        "id",
        "account_id",
        "ticket_id",
        "ticket_number",
        "assignee_id",
        "created_by",
        "modified_by",
        "deal_owner_id",
        "crm_deal_id",
    )
    def serialize_ids(self, value):
        return str(value) if value is not None else None

class DealCreationBody(BaseModel):

    # Primary Key
    id: Optional[int] = None
    # Relationship
    account_id: int

    # Deal & Ticket InfoS
    ticket_id: Optional[int] = None
    ticket_number: Optional[int] = None
    deal_type: Optional[str] = None
    loan_type: Optional[str] = None
    type_of_login: Optional[str] = None
    type_of_case_login: Optional[str] = None
    ticket_login: Optional[bool] = None
    case_stage: Optional[str] = None
    case_status: Optional[str] = None

    # Amounts
    disbursed_amount: Optional[Decimal] = None
    sanction_amount: Optional[Decimal] = None
    approved_amount: Optional[Decimal] = None
    amount_required: Optional[Decimal] = None
    processing_fees: Optional[Decimal] = None
    mm_charges: Optional[Decimal] = None
    insurance_amount: Optional[Decimal] = None
    pf_percentage: Optional[Decimal] = None
    rate_of_interest: Optional[Decimal] = None
    interest_type: Optional[str] = None

    # Dates
    deal_call_back_datetime: Optional[datetime] = None
    disbursement_date: Optional[date] = None
    lender_login_date: Optional[date] = None
    loan_start_date: Optional[date] = None
    loan_end_date: Optional[date] = None
    targeted_disbursement_date: Optional[date] = None
    tenure: Optional[int] = None

    # Lender / Rejection
    lender_code: Optional[str] = None
    lender_name: Optional[str] = None
    customer_rejection_reason: Optional[str] = None
    customer_rejection_status_explanation: Optional[str] = None
    lender_rejection_reason: Optional[str] = None
    lender_rejection_status_explanation: Optional[str] = None

    # Attachments
    payment_receipt: Optional[Any] = None
    sanction_letter: Optional[str] = None
    potential: Optional[str] = None
    product: Optional[str] = None

    # Audit
    assignee_id: Optional[int] = None
    created_by: Optional[int] = None
    modified_by: Optional[int] = None

    # Account
    account_name: str

    # Timestamps
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(IST))
    updated_at: Optional[datetime] = None
    deal_owner_id: Optional[int] = None
    crm_deal_id: Optional[int] = None

    model_config = {
        "from_attributes": True
    }

    # ---- ID Serializers ----
    @field_serializer(
        "id",
        "account_id",
        "ticket_id",
        "ticket_number",
        "assignee_id",
        "created_by",
        "modified_by",
        "deal_owner_id",
        "crm_deal_id",
    )
    def serialize_ids(self, value):
        return int(value) if value is not None else None


@field_serializer("deal_call_back_datetime")
def serialize_datetime(self, value) -> Optional[str]:
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=IST)
        return value.astimezone(IST).strftime("%Y-%m-%dT%H:%M:%S")

    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=IST)
        return parsed.astimezone(IST).strftime("%Y-%m-%dT%H:%M:%S")
    return None