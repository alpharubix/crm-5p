from sqlalchemy.orm import Session
from ..models.audit_log import AuditLog

def log_action(db: Session, user_id: int, user_role: str, action: str, entity: str, entity_id: int, payload: dict):
    log = AuditLog(
        user_id=user_id,
        user_role=user_role,
        action=action,
        entity=entity,
        entity_id=entity_id,
        payload=payload,
    )
    db.add(log)
    db.commit()