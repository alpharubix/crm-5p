from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import BIGINT, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Contact(Base):
    __tablename__ = "contacts_5p"

    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    
    # FIXED: Bound to accounts_5p table
    account_id = Column(BIGINT, ForeignKey("accounts_5p.id"), index=True)
    owner_id = Column(BIGINT, ForeignKey("users.id"), index=True)

    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    designation = Column(String, nullable=True)

    email = Column(String, nullable=True, index=True)
    secondary_email = Column(String, nullable=True)
    mobile = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    lead_source = Column(String, nullable=True, index=True)

    street = Column(String, nullable=True)
    city = Column(String, nullable=True, index=True)
    state = Column(String, nullable=True, index=True)
    country = Column(String, nullable=True)
    pincode = Column(String, nullable=True)

    custom_fields = Column(JSONB, default={}, nullable=False)

    created_by_id = Column(BIGINT, ForeignKey("users.id"), nullable=True)
    modified_by_id = Column(BIGINT, ForeignKey("users.id"), nullable=True)
    created_time = Column(DateTime(timezone=True), server_default=func.now())
    modified_time = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    contact_owner = relationship(
        "User", foreign_keys=[owner_id], backref="contact_owner"
    )
    
    # FIXED: Changed "Account5P" to "Account" to match your standalone project's class name
    parent_account = relationship(
        "Account", foreign_keys=[account_id], backref="account_linked_contact"
    )
    
    created_by = relationship(
        "User", foreign_keys=[created_by_id], backref="contact_created_by"
    )
    modified_by = relationship(
        "User", foreign_keys=[modified_by_id], backref="contact_modified_by"
    )