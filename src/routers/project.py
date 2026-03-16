from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo
from ..database import get_db
from ..models.project import Project, Task

IST = ZoneInfo("Asia/Kolkata")
router = APIRouter(prefix="/projects", tags=["projects"])


def format_project(p) -> dict:
    return {
        "id": str(p.id),
        "name": p.name,
        "description": p.description,
        "priority": p.priority,
        "status": p.status,
        "created_by": str(p.created_by),
        "modified_by": str(p.modified_by) if p.modified_by else None,
        "created_at": p.created_at.astimezone(IST).strftime("%d %b %Y, %I:%M %p"),
        "modified_at": p.modified_at.astimezone(IST).strftime("%d %b %Y, %I:%M %p") if p.modified_at else None,
        "start_date": p.start_date.strftime("%Y-%m-%d") if p.start_date else None,
        "end_date":   p.end_date.strftime("%Y-%m-%d") if p.end_date else None,
        "actioner_ids": [str(i) for i in (p.actioner_ids or [])],
        "project_type": p.project_type
    }


@router.post("")
@router.post("/")
async def create_project(request: Request, db: Session = Depends(get_db)):

    # Allowed users roles - [super_admin,admin]
    if request.state.role== "executive" :
        raise HTTPException(status_code=401, detail="Unauthorized access")

    body = await request.json()

    if not body.get("name"):
        raise HTTPException(status_code=400, detail="name is required")

    project = Project(
        name        = body["name"],
        description = body.get("description"),
        priority    = body.get("priority"),
        status = body.get("status", "pending_for_approve"),
        created_by  = request.state.user_id,
        start_date  = body.get("start_date"),
        end_date    = body.get("end_date"),
        actioner_ids = body.get("actioner_ids", []),
        project_type = body.get("project_type")
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return format_project(project)


@router.get("")
@router.get("/")
def get_projects(request: Request,page: int = 1, db: Session = Depends(get_db)):
    if request.state.role=="executive":
        raise HTTPException(status_code=401, detail="Unauthorised Access")

    limit  = 20
    offset = (page - 1) * limit
    total  = db.query(Project).count()
    
    projects = (
        db.query(Project)
        .order_by(Project.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "data": [format_project(p) for p in projects],
        "page_info": {"page": page, "total": total},
    }


@router.get("/{project_id}")
def get_project(request:Request, project_id: int, db: Session = Depends(get_db)):
    if request.state.role=="executive":
        raise HTTPException(status_code=401, detail="Unathorised Access")

    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return format_project(project)


@router.patch("/{project_id}")
async def update_project(project_id: int, request: Request, db: Session = Depends(get_db)):
    if request.state.role=="executive":
        raise HTTPException(status_code=401, detail="Unauthorised Access")
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    body = await request.json()
    allowed = ["name", "description", "priority", "status", "actioner_ids", "project_type"]

    for field in allowed:
        if field in body:
            setattr(project, field, body[field])

    if "start_date" in body:
        project.start_date = body["start_date"]
    if "end_date" in body:
        project.end_date = body["end_date"]

    project.modified_by = request.state.user_id
    db.commit()
    db.refresh(project)

    return format_project(project)


@router.delete("/{project_id}")
def delete_project(project_id: int, request: Request, db: Session = Depends(get_db)):
    if request.state.role=="executive":
        raise HTTPException(status_code=401,detail="Unauthorised access")
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()

    return {"message": "Project deleted"}





def format_task(t) -> dict:
    return {
        "id": str(t.id),
        "title": t.title,
        "description": t.description,
        "type": t.type,
        "priority": t.priority,
        "status": t.status,
        "project_id": str(t.project_id),
        "assignee_id": str(t.assignee_id) if t.assignee_id else None,
        "created_by": str(t.created_by),
        "modified_by": str(t.modified_by) if t.modified_by else None,
        "created_at": t.created_at.astimezone(IST).strftime("%d %b %Y, %I:%M %p"),
        "modified_at": t.modified_at.astimezone(IST).strftime("%d %b %Y, %I:%M %p") if t.modified_at else None,
        "assignee_name": t.assignee.full_name if t.assignee else None,
    }


@router.post("/{project_id}/tasks")
async def create_task(project_id: int, request: Request, db: Session = Depends(get_db)):
 
    if request.state.role=="executive":
        raise HTTPException(status_code=401, detail="Unauthorised Access")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    body = await request.json()

    if not body.get("title"):
        raise HTTPException(status_code=400, detail="title is required")

    task = Task(
        title       = body["title"],
        description = body.get("description"),
        type        = body.get("type", "feature"),
        priority    = body.get("priority"),
        status      = body.get("status", "todo"),
        project_id  = project_id,
        assignee_id = body.get("assignee_id"),
        created_by  = request.state.user_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return format_task(task)


@router.get("/{project_id}/tasks")
def get_tasks(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks = (
        db.query(Task)
        .filter(Task.project_id == project_id)
        .order_by(Task.created_at.desc())
        .all()
    )

    return {"data": [format_task(t) for t in tasks]}


@router.patch("/{project_id}/tasks/{task_id}")
async def update_task(project_id: int, task_id: int, request: Request, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    body = await request.json()
    allowed = ["title", "description", "type", "priority", "status", "assignee_id"]

    for field in allowed:
        if field in body:
            setattr(task, field, body[field])

    task.modified_by = request.state.user_id
    db.commit()
    db.refresh(task)

    return format_task(task)


@router.delete("/{project_id}/tasks/{task_id}")
def delete_task(project_id: int, task_id: int, request: Request, db: Session = Depends(get_db)):
    if request.status.role=="executive":
        raise HTTPException(status_code=401, detail="Unauthorised Access")
    
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    return {"message": "Task deleted"}