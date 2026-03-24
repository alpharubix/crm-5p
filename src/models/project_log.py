from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, BigInteger
from sqlalchemy.sql import func
from ..database import Base

class ProjectLog(Base):
    __tablename__ = "project_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Hierarchy Tracking
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    
    # Who did it
    user_id = Column(BigInteger, nullable=False)
    user_role = Column(String, nullable=False)
    
    # What happened
    action = Column(String, nullable=False) # e.g., "CREATED", "STATUS_UPDATED", "COMMENTED"
    entity_type = Column(String, nullable=False) # e.g., "PROJECT", "TASK", "COMMENT"
    
    # The actual data changes (Important for tracking old vs new status)
    changes = Column(JSON, nullable=True) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())