from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator, model_validator

from auth_models import AuthCredentials
from auth_service import login_user, signup_user

from database import (
    delete_task_record,
    fetch_all_tasks,
    fetch_task,
    initialize_database,
    insert_task,
    update_task_record,
)

initialize_database()

app = FastAPI(
    title="Task API",
    version="1.0.0",
    description=(
        "A Postgres-backed CRUD API for managing tasks. "
        "Data persists across app and container restarts."
    ),
    docs_url="/docs",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "System", "description": "API information and health checks"},
        {"name": "Tasks", "description": "Create, read, update, and delete tasks"},
        {"name": "Authentication", "description": "Supabase sign up and login"},
    ],
)


class TaskCreate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Title is required and cannot be empty")
        return value.strip()


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Title must be a non-empty string")
        return value.strip() if value is not None else None

    @model_validator(mode="after")
    def require_a_field(self):
        if "title" not in self.model_fields_set and "done" not in self.model_fields_set:
            raise ValueError("Provide a title and/or done value")
        return self


def find_task(task_id: int) -> dict[str, object]:
    task = fetch_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    first_error = exc.errors()[0]
    message = first_error.get("msg", "Invalid request body")
    if message.startswith("Value error, "):
        message = message.removeprefix("Value error, ")
    return JSONResponse(status_code=400, content={"error": message})


@app.get("/", tags=["System"], summary="Get API information")
def api_info():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", tags=["System"], summary="Check server health")
def health_check():
    return {"status": "ok"}




@app.post(
    "/auth/signup",
    status_code=201,
    tags=["Authentication"],
    summary="Create a Supabase user account",
)
def auth_signup(payload: AuthCredentials):
    return signup_user(payload.email, payload.password)


@app.post(
    "/auth/login",
    tags=["Authentication"],
    summary="Log in and receive Supabase tokens",
)
def auth_login(payload: AuthCredentials):
    return login_user(payload.email, payload.password)

@app.get("/tasks", tags=["Tasks"], summary="List all tasks")
def list_tasks():
    return fetch_all_tasks()


@app.get("/tasks/{task_id}", tags=["Tasks"], summary="Get one task")
def get_task(task_id: int):
    return find_task(task_id)


@app.post("/tasks", status_code=201, tags=["Tasks"], summary="Create a task")
def create_task(payload: TaskCreate):
    return insert_task(payload.title)


@app.put("/tasks/{task_id}", tags=["Tasks"], summary="Update a task")
def update_task(task_id: int, payload: TaskUpdate):
    task = update_task_record(
        task_id,
        title=payload.title,
        done=payload.done,
        update_title="title" in payload.model_fields_set,
        update_done="done" in payload.model_fields_set,
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/tasks/{task_id}", status_code=204, tags=["Tasks"], summary="Delete a task")
def delete_task(task_id: int):
    if not delete_task_record(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=204)
