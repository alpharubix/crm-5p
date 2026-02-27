from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.audit_log import AuditLog

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("")
def get_audit_logs(request: Request, page: int = 1, db: Session = Depends(get_db)):
    if request.state.role != "super_admin":
        raise HTTPException(status_code=403, detail="Access denied")

    limit = 20
    offset = (page - 1) * limit

    total = db.query(AuditLog).count()
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "data": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "user_role": log.user_role,
                "action": log.action,
                "entity": log.entity,
                "entity_id": log.entity_id,
                "payload": log.payload,
                "created_at": log.created_at.strftime("%d %b %Y, %I:%M %p"),
            }
            for log in logs
        ],
        "page_info": {"page": page, "total": total},
    }
