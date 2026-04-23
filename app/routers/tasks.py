from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.schemas import TaskCreate, TaskUpdate, TaskOut
from app.models import User, Task, Category

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _validate_category(db: Session, category_id: Optional[int], user_id: int) -> None:
    if category_id is None:
        return
    exists = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == user_id,
    ).first()
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found",
        )


@router.get("/", response_model=list[TaskOut])
def list_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = Query("created_at"),
    order: Optional[str] = Query("desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Task).filter(Task.user_id == current_user.id)

    if status_filter:
        query = query.filter(Task.status == status_filter)
    if priority:
        query = query.filter(Task.priority == priority)
    if category_id is not None:
        query = query.filter(Task.category_id == category_id)
    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    allowed_sort = {"created_at", "updated_at", "due_date", "title", "priority", "status"}
    if sort_by not in allowed_sort:
        sort_by = "created_at"

    sort_column = getattr(Task, sort_by)
    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    return query.all()


@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_category(db, data.category_id, current_user.id)
    task = Task(
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        due_date=data.due_date,
        category_id=data.category_id,
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id,
    ).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id,
    ).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    update_data = data.model_dump(exclude_unset=True)
    if "category_id" in update_data:
        _validate_category(db, update_data["category_id"], current_user.id)

    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id,
    ).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    db.delete(task)
    db.commit()
