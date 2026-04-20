from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request
from src.database import get_db
from src.models.deal_document import DealDocument
from datetime import datetime, timezone

deal_docs_router = APIRouter(prefix="/deals/{deal_id}/documents", tags=["deal-documents"])


def format_doc(d: DealDocument) -> dict:
    return {
        "id": str(d.id),
        "deal_id": str(d.deal_id),
        "module": d.module,
        "description": d.description,
        "from_date": d.from_date,
        "to_date": d.to_date,
        "status": d.status,
        "link": d.link,
        "created_by": str(d.created_by) if d.created_by is not None else None,
        "modified_by": str(d.modified_by) if d.modified_by is not None else None,
        "created_at": d.created_at.isoformat() if d.created_at is not None else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at is not None else None,
    }


@deal_docs_router.get("")
@deal_docs_router.get("/")
def get_documents(deal_id: int, db: Session = Depends(get_db)):
    docs = db.query(DealDocument).filter(DealDocument.deal_id == deal_id).all()
    return {"data": [format_doc(d) for d in docs]}


@deal_docs_router.post("")
@deal_docs_router.post("/")
async def create_document(deal_id: int, request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    sanitized_body = {k: (v if v != "" else None) for k, v in body.items()}
    doc = DealDocument(
        deal_id=deal_id,
        module=body.get("module"),
        description=body.get("description"),
        from_date=sanitized_body.get("from_date"),
        to_date=sanitized_body.get("to_date"),
        status=body.get("status"),
        link=body.get("link"),
        created_by=request.state.user_id,
        modified_by=request.state.user_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return format_doc(doc)


@deal_docs_router.put("/{doc_id}")
async def update_document(deal_id: int, doc_id: int, request: Request, db: Session = Depends(get_db)):
    doc = db.query(DealDocument).filter(
        DealDocument.id == doc_id,
        DealDocument.deal_id == deal_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    body = await request.json()
    for key in ("module", "description", "from_date", "to_date", "status", "link"):
        if key in body:
            setattr(doc, key, body[key])

    doc.modified_by = request.state.user_id
    doc.updated_at = datetime.now(timezone.utc)  # type: ignore
    db.commit()
    db.refresh(doc)
    return format_doc(doc)


@deal_docs_router.delete("/{doc_id}")
def delete_document(deal_id: int, doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(DealDocument).filter(
        DealDocument.id == doc_id,
        DealDocument.deal_id == deal_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"message": "deleted"}