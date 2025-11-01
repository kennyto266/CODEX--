#!/usr/bin/env python3
"""
Simple Task API
提供简单的任务API端点，直接从SQLite读取数据
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import uvicorn
from pathlib import Path
from datetime import datetime

app = FastAPI(title="Task Management API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Task(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    estimated_hours: int = 0
    actual_hours: int = 0
    stage: Optional[str] = None
    section: Optional[str] = None
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    sprint: Optional[str] = None
    story_points: int = 1
    progress_percentage: float = 0.0
    is_blocked: bool = False
    is_completed: bool = False

    class Config:
        orm_mode = True

class TaskSummary(BaseModel):
    total: int
    completed: int
    in_progress: int
    blocked: int
    todo: int
    completion_rate: float

def get_db_connection():
    """Get SQLite database connection"""
    db_path = Path('tasks.db')
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="Database not found")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Task Management API",
        "version": "1.0.0",
        "endpoints": {
            "tasks": "/tasks",
            "task_by_id": "/tasks/{task_id}",
            "summary": "/tasks/summary"
        }
    }

@app.get("/tasks/summary", response_model=TaskSummary, tags=["tasks"])
async def get_task_summary():
    """Get task summary statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get counts
        cursor.execute("SELECT COUNT(*) FROM tasks")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = '已完成'")
        completed = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = '进行中'")
        in_progress = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'TODO'")
        todo = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE is_blocked = 1")
        blocked = cursor.fetchone()[0]

        # Calculate completion rate
        completion_rate = (completed / total * 100) if total > 0 else 0

        conn.close()

        return TaskSummary(
            total=total,
            completed=completed,
            in_progress=in_progress,
            todo=todo,
            blocked=blocked,
            completion_rate=round(completion_rate, 1)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks", response_model=List[Task], tags=["tasks"])
async def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: Optional[int] = 100
):
    """Get all tasks with optional filtering"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        query = "SELECT * FROM tasks"
        params = []

        if status or priority:
            query += " WHERE"
            conditions = []

            if status:
                conditions.append(" status = ?")
                params.append(status)

            if priority:
                conditions.append(" priority = ?")
                params.append(priority)

            query += " AND".join(conditions)

        query += " ORDER BY id"
        query += f" LIMIT {limit}"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to Task objects
        tasks = []
        for row in rows:
            task = Task(
                id=row['id'],
                title=row['title'],
                description=row['description'],
                status=row['status'],
                priority=row['priority'],
                estimated_hours=row['estimated_hours'],
                actual_hours=row['actual_hours'],
                stage=row['stage'],
                section=row['section'],
                assignee=row['assignee'],
                reporter=row['reporter'],
                sprint=row['sprint'],
                story_points=row['story_points'],
                progress_percentage=row['progress_percentage'],
                is_blocked=bool(row['is_blocked']),
                is_completed=bool(row['is_completed'])
            )
            tasks.append(task)

        conn.close()
        return tasks

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{task_id}", response_model=Task, tags=["tasks"])
async def get_task(task_id: str):
    """Get a single task by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        task = Task(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            status=row['status'],
            priority=row['priority'],
            estimated_hours=row['estimated_hours'],
            actual_hours=row['actual_hours'],
            stage=row['stage'],
            section=row['section'],
            assignee=row['assignee'],
            reporter=row['reporter'],
            sprint=row['sprint'],
            story_points=row['story_points'],
            progress_percentage=row['progress_percentage'],
            is_blocked=bool(row['is_blocked']),
            is_completed=bool(row['is_completed'])
        )

        conn.close()
        return task

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/tasks", response_model=Task, tags=["tasks"])
async def create_task(task: Task):
    """Create a new task"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if task ID already exists
        cursor.execute("SELECT id FROM tasks WHERE id = ?", (task.id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"Task {task.id} already exists")

        # Insert new task
        cursor.execute("""
            INSERT INTO tasks (
                id, title, description, status, priority,
                estimated_hours, actual_hours, stage, section,
                assignee, reporter, sprint, story_points,
                progress_percentage, is_blocked, is_completed,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.id, task.title, task.description, task.status, task.priority,
            task.estimated_hours, task.actual_hours, task.stage, task.section,
            task.assignee, task.reporter, task.sprint, task.story_points,
            task.progress_percentage, task.is_blocked, task.is_completed,
            datetime.now().isoformat(), datetime.now().isoformat()
        ))
        conn.commit()

        # Get created task
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task.id,))
        row = cursor.fetchone()

        conn.close()

        return Task(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            status=row['status'],
            priority=row['priority'],
            estimated_hours=row['estimated_hours'],
            actual_hours=row['actual_hours'],
            stage=row['stage'],
            section=row['section'],
            assignee=row['assignee'],
            reporter=row['reporter'],
            sprint=row['sprint'],
            story_points=row['story_points'],
            progress_percentage=row['progress_percentage'],
            is_blocked=bool(row['is_blocked']),
            is_completed=bool(row['is_completed'])
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/tasks/{task_id}/status", response_model=Task, tags=["tasks"])
async def update_task_status(task_id: str, new_status: str):
    """Update task status"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if task exists
        cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Update status
        cursor.execute(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, datetime.now().isoformat(), task_id)
        )
        conn.commit()

        # Get updated task
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()

        conn.close()

        if row:
            task = Task(
                id=row['id'],
                title=row['title'],
                description=row['description'],
                status=row['status'],
                priority=row['priority'],
                estimated_hours=row['estimated_hours'],
                actual_hours=row['actual_hours'],
                stage=row['stage'],
                section=row['section'],
                assignee=row['assignee'],
                reporter=row['reporter'],
                sprint=row['sprint'],
                story_points=row['story_points'],
                progress_percentage=row['progress_percentage'],
                is_blocked=bool(row['is_blocked']),
                is_completed=bool(row['is_completed'])
            )
            return task
        else:
            raise HTTPException(status_code=500, detail="Failed to update task")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("="*60)
    print("Starting Task Management API Server")
    print("="*60)
    print()
    print("API Documentation: http://localhost:8000/docs")
    print("Tasks Endpoint: http://localhost:8000/tasks")
    print("Task Summary: http://localhost:8000/tasks/summary")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
