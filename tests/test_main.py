import json


def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_ready_returns_ready(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ready"


def test_metrics_endpoint_exposes_prometheus_format(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "app_info" in body


def test_every_response_carries_a_request_id_header(client):
    resp = client.get("/health")
    assert "X-Request-ID" in resp.headers


def test_request_id_is_echoed_back_when_supplied(client):
    resp = client.get("/health", headers={"X-Request-ID": "test-fixed-id"})
    assert resp.headers["X-Request-ID"] == "test-fixed-id"


def test_create_task_success(client):
    resp = client.post("/api/tasks", json={"title": "Write CI pipeline"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["title"] == "Write CI pipeline"
    assert body["status"] == "todo"
    assert isinstance(body["id"], int)


def test_create_task_missing_title_returns_400(client):
    resp = client.post("/api/tasks", json={})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"]["code"] == "validation_error"


def test_create_task_rejects_invalid_status(client):
    resp = client.post("/api/tasks", json={"title": "x", "status": "blocked"})
    assert resp.status_code == 400


def test_list_tasks_returns_created_tasks(client):
    client.post("/api/tasks", json={"title": "first"})
    client.post("/api/tasks", json={"title": "second"})
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["count"] >= 2


def test_list_tasks_filters_by_status(client):
    client.post("/api/tasks", json={"title": "a", "status": "done"})
    resp = client.get("/api/tasks?status=done")
    body = resp.get_json()
    assert all(t["status"] == "done" for t in body["tasks"])


def test_list_tasks_rejects_bad_limit(client):
    resp = client.get("/api/tasks?limit=999")
    assert resp.status_code == 400


def test_get_missing_task_returns_404_with_json_shape(client):
    resp = client.get("/api/tasks/999999")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"]["code"] == "not_found"


def test_update_task_changes_title_and_status(client):
    created = client.post("/api/tasks", json={"title": "old"}).get_json()
    resp = client.patch(f"/api/tasks/{created['id']}", json={"title": "new", "status": "done"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["title"] == "new"
    assert body["status"] == "done"


def test_delete_task_then_404_on_refetch(client):
    created = client.post("/api/tasks", json={"title": "temp"}).get_json()
    delete_resp = client.delete(f"/api/tasks/{created['id']}")
    assert delete_resp.status_code == 204
    refetch = client.get(f"/api/tasks/{created['id']}")
    assert refetch.status_code == 404


def test_unknown_route_returns_consistent_error_shape(client):
    resp = client.get("/does/not/exist")
    assert resp.status_code == 404
    body = resp.get_json()
    assert "error" in body and "code" in body["error"]


def test_store_unit_validation_errors_directly():
    from app.store import TaskStore, ValidationError

    store = TaskStore()
    try:
        store.create(title="   ")
        assert False, "expected ValidationError"
    except ValidationError as exc:
        assert "blank" in exc.message

    body = json.dumps({"ok": True})
    assert body  # keeps json import meaningfully used in this module
