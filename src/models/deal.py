from sqlalchemy import (BigInteger, Boolean, Column, Date, Integer,
                        Numeric, String, Text, DateTime, func)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase
from ..database import Base



class Deal(Base):
    __tablename__ = "deals"

    # Primary Key
    id                  = Column(BigInteger, primary_key=True, autoincrement=True)

    # Deal & Ticket Info
    ticket_id           = Column(Integer)
    ticket_number       = Column(BigInteger)
    deal_type           = Column(String(100))
    loan_type           = Column(String(150))
    type_of_login       = Column(String(50))
    type_of_case_login  = Column(String(50))
    ticket_login        = Column(Boolean, default=False)
    case_stage          = Column(String(50))
    case_status         = Column(String(50))

    # Amounts
    disbursed_amount    = Column(Numeric(15, 2))
    sanction_amount     = Column(Numeric(15, 2))
    approved_amount     = Column(Numeric(15, 2))
    amount_required     = Column(Numeric(15, 2))
    processing_fees     = Column(Numeric(15, 2))
    mm_charges          = Column(Numeric(15, 2))
    insurance_amount    = Column(Numeric(15, 2))
    pf_percentage       = Column(Numeric(5, 2))
    rate_of_interest    = Column(Numeric(5, 2))
    interest_type       = Column(String(50))

    # Dates
    deal_call_back_datetime     = Column(Date)
    disbursement_date           = Column(Date)
    lender_login_date           = Column(Date)
    loan_start_date             = Column(Date)
    loan_end_date               = Column(Date)
    targeted_disbursement_date  = Column(Date)
    tenure                      = Column(Integer)

    # Lender / Rejection
    lender_code                             = Column(String(100))
    lender_name                             = Column(String(150))
    customer_rejection_reason               = Column(Text)
    customer_rejection_status_explanation   = Column(Text)
    lender_rejection_reason                 = Column(Text)
    lender_rejection_status_explanation     = Column(Text)

    # Attachments
    payment_receipt     = Column(JSONB)
    sanction_letter     = Column(Text)
    potential           = Column(Text)
    product             = Column(Text)

    # Audit
    assignee_id         = Column(BigInteger)
    created_by          = Column(BigInteger)
    modified_by         = Column(BigInteger)

    # Account
    account_id          = Column(BigInteger)
    account_name        = Column(String(100))

    # Timestamps
    created_at          = Column(DateTime, nullable=False, server_default=func.now())
    updated_at          = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    deal_owner_id       = Column(BigInteger)