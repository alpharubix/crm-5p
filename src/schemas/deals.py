from pydantic import BaseModel, field_serializer
from typing import Optional, Any
from datetime import date, datetime
from decimal import Decimal


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
    loan_start_date: Optional[date]
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
        "deal_owner_id"
    )
    def serialize_ids(self, value):
        return str(value) if value is not None else None