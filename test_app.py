import pytest
from fastapi.testclient import TestClient

import app_final
from app_final import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_storage():
    """Перед каждым тестом очищаем список задач."""
    app_final.tasks.clear()
    app_final.next_id = 1


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version():
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()


def test_create_and_list_tasks():
    response = client.post("/tasks", json={"title": "Купить молоко"})
    assert response.status_code == 201
    assert response.json()["title"] == "Купить молоко"

    tasks = client.get("/tasks").json()
    assert len(tasks) == 1


def test_get_task_by_id():
    client.post("/tasks", json={"title": "Сделать проект"})
    response = client.get("/tasks/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_missing_task_returns_404():
    response = client.get("/tasks/999")
    assert response.status_code == 404


def test_complete_task_and_filter():
    client.post("/tasks", json={"title": "Задача 1"})
    client.post("/tasks", json={"title": "Задача 2"})
    client.post("/tasks/1/done")

    done = client.get("/tasks?done=true").json()
    assert [t["id"] for t in done] == [1]


def test_empty_title_is_rejected():
    response = client.post("/tasks", json={"title": ""})
    assert response.status_code == 422


def test_stats():
    client.post("/tasks", json={"title": "Первая"})
    client.post("/tasks", json={"title": "Вторая"})
    client.post("/tasks/1/done")
    assert client.get("/stats").json() == {"total": 2, "done": 1, "open": 1}


def test_delete_task():
    client.post("/tasks", json={"title": "Удалить меня"})
    assert client.delete("/tasks/1").status_code == 200
    assert client.get("/tasks/1").status_code == 404
