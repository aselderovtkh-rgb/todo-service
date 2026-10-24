"""Todo Service — простой сервис списка задач на FastAPI.

Основа: учебный пример app_final.py с занятий (переработан под свою тему).
Задачи хранятся в памяти процесса: после перезапуска список очищается.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ---------- Настройки из переменных окружения ----------
APP_NAME = os.getenv("APP_NAME", "Todo Service")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
MAX_TASKS = int(os.getenv("MAX_TASKS", "100"))

# ---------- Логирование ----------
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("todo")

# ---------- Хранилище в памяти ----------
tasks: dict[int, dict] = {}
next_id = 1


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск %s v%s (MAX_TASKS=%s)", APP_NAME, APP_VERSION, MAX_TASKS)
    yield
    logger.info("Остановка %s", APP_NAME)


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)


# ---------- Служебные маршруты ----------
@app.get("/")
def root():
    return {"message": f"{APP_NAME} работает. Документация: /docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"name": APP_NAME, "version": APP_VERSION}


# ---------- Маршруты по теме ----------
@app.get("/tasks")
def list_tasks(done: bool | None = None):
    """Список задач. Можно отфильтровать: /tasks?done=true или ?done=false."""
    result = list(tasks.values())
    if done is not None:
        result = [t for t in result if t["done"] == done]
    return result


@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    global next_id
    if len(tasks) >= MAX_TASKS:
        logger.warning("Отказ: достигнут лимит задач (%s)", MAX_TASKS)
        raise HTTPException(status_code=400, detail="Достигнут лимит задач")
    task = {"id": next_id, "title": payload.title, "done": False}
    tasks[next_id] = task
    next_id += 1
    logger.info("Создана задача id=%s: %s", task["id"], task["title"])
    return task


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = tasks.get(task_id)
    if task is None:
        logger.warning("Задача id=%s не найдена", task_id)
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


@app.post("/tasks/{task_id}/done")
def complete_task(task_id: int):
    task = get_task(task_id)
    task["done"] = True
    logger.info("Задача id=%s выполнена", task_id)
    return task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    get_task(task_id)
    del tasks[task_id]
    logger.info("Задача id=%s удалена", task_id)
    return {"deleted": task_id}
