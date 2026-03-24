from sqlalchemy.orm import Session
from ..models.project_log import ProjectLog

def log_project_action(
    db: Session, 
    user_id: int, 
    user_role: str, 
    action: str, 
    entity_type: str, 
    project_id: int, 
    task_id: int | None = None, 
    changes: dict | None = None
):
    log = ProjectLog(
        user_id=user_id,
        user_role=user_role,
        action=action,
        entity_type=entity_type,
        project_id=project_id,
        task_id=task_id,
        changes=changes or {}
    )
    db.add(log)
    db.commit()