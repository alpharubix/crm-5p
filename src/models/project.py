from sqlalchemy import Column, BigInteger, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from ..database import Base


class PriorityEnum(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class StatusEnum(str, enum.Enum):
    planning = "planning"
    active = "active"
    on_hold = "on_hold"
    completed = "completed"
    cancelled = "cancelled"


class TaskStatusEnum(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    review = "review"
    done = "done"


class TaskTypeEnum(str, enum.Enum):
    feature = "feature"
    bug = "bug"
    enhancement = "enhancement"
    research = "research"


class Project(Base):
    __tablename__ = "projects"

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    name        = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority    = Column(Enum(PriorityEnum), nullable=True)
    status      = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.planning)
    created_by  = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    modified_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    modified_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    modifier = relationship("User", foreign_keys=[modified_by])
    creator = relationship("User", foreign_keys=[created_by])
    tasks = relationship("Task", back_populates="project")



class Task(Base):
    __tablename__ = "tasks"

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    title       = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type        = Column(Enum(TaskTypeEnum), nullable=False, default=TaskTypeEnum.feature)
    priority    = Column(Enum(PriorityEnum), nullable=True)
    status      = Column(Enum(TaskStatusEnum), nullable=False, default=TaskStatusEnum.todo)
    project_id  = Column(BigInteger, ForeignKey("projects.id"), nullable=False)
    assignee_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_by  = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    modified_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    modified_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    project     = relationship("Project", back_populates="tasks")
    assignee    = relationship("User", foreign_keys=[assignee_id])
    creator     = relationship("User", foreign_keys=[created_by])
    modifier    = relationship("User", foreign_keys=[modified_by])


