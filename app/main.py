"""Flask application factory and routes.

Run directly with `python -m app.main` for local debugging (Flask's dev
server), or behind gunicorn in Docker/production via `gunicorn_conf.py`.
"""

import logging
import time
import uuid
from typing import Tuple

from flask import Flask, g, jsonify, request
from prometheus_client import CollectorRegistry
from prometheus_flask_exporter import PrometheusMetrics
from werkzeug.exceptions import HTTPException

from app.logging_config import configure_logging
from app.store import TaskNotFoundError, TaskStore, ValidationError

logger = logging.getLogger("app")


def create_app() -> Flask:
    configure_logging()

    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False
    app.store = TaskStore()  # type: ignore[attr-defined]

    # Each call to create_app() gets its own CollectorRegistry. Without
    # this, a second app instance in the same process (every test fixture
    # does exactly that) tries to register "app_info" on the shared global
    # registry and prometheus_client raises a duplicate-timeseries error.
    registry = CollectorRegistry()
    metrics = PrometheusMetrics(app, path="/metrics", registry=registry)
    metrics.info("app_info", "Task Tracker API build info", version="2.0.0")

    register_request_logging(app)
    register_routes(app)
    register_error_handlers(app)

    return app


def register_request_logging(app: Flask) -> None:
    @app.before_request
    def _start_timer() -> None:
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        g.start_time = time.time()

    @app.after_request
    def _log_and_tag(response):
        elapsed = time.time() - g.get("start_time", time.time())
        duration_ms = round(elapsed * 1000, 2)
        response.headers["X-Request-ID"] = g.get("request_id", "unknown")
        logger.info(
            "request handled",
            extra={
                "request_id": g.get("request_id"),
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response


def register_routes(app: Flask) -> None:
    @app.get("/health")
    def health() -> Tuple[dict, int]:
        # Liveness: is the process up and able to answer at all. Anything
        # heavier (DB ping, downstream calls) belongs in /ready, not here,
        # otherwise a slow dependency takes down the orchestrator's
        # liveness check and triggers a pointless restart loop.
        return jsonify({"status": "ok"}), 200

    @app.get("/ready")
    def ready() -> Tuple[dict, int]:
        # Readiness: can this instance actually serve traffic right now.
        # There's no external dependency in this demo, so this checks the
        # one thing that could plausibly be in a bad state: the store.
        try:
            app.store.count()  # type: ignore[attr-defined]
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("readiness check failed", extra={"error": str(exc)})
            return jsonify({"status": "not_ready"}), 503
        return jsonify({"status": "ready"}), 200

    @app.get("/api/tasks")
    def list_tasks():
        status = request.args.get("status")
        limit = request.args.get("limit", default=50, type=int)
        offset = request.args.get("offset", default=0, type=int)
        tasks = app.store.list(  # type: ignore[attr-defined]
            status=status, limit=limit, offset=offset
        )
        return jsonify({"tasks": tasks, "count": len(tasks)}), 200

    @app.post("/api/tasks")
    def create_task():
        body = request.get_json(silent=True) or {}
        task = app.store.create(  # type: ignore[attr-defined]
            title=body.get("title", ""), status=body.get("status", "todo")
        )
        return jsonify(task), 201

    @app.get("/api/tasks/<int:task_id>")
    def get_task(task_id: int):
        task = app.store.get(task_id)  # type: ignore[attr-defined]
        return jsonify(task), 200

    @app.patch("/api/tasks/<int:task_id>")
    def update_task(task_id: int):
        body = request.get_json(silent=True) or {}
        task = app.store.update(  # type: ignore[attr-defined]
            task_id, title=body.get("title"), status=body.get("status")
        )
        return jsonify(task), 200

    @app.delete("/api/tasks/<int:task_id>")
    def delete_task(task_id: int):
        app.store.delete(task_id)  # type: ignore[attr-defined]
        return "", 204


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ValidationError)
    def _validation_error(err: ValidationError):
        return _error_response(400, "validation_error", err.message)

    @app.errorhandler(TaskNotFoundError)
    def _not_found_error(err: TaskNotFoundError):
        return _error_response(404, "not_found", str(err))

    @app.errorhandler(HTTPException)
    def _http_error(err: HTTPException):
        return _error_response(err.code or 500, "http_error", err.description or "")

    @app.errorhandler(Exception)
    def _unhandled_error(err: Exception):
        logger.exception("unhandled exception", extra={"request_id": g.get("request_id")})
        return _error_response(500, "internal_error", "an unexpected error occurred")


def _error_response(status: int, code: str, message: str):
    return jsonify({"error": {"code": code, "message": message}}), status


app = create_app()

if __name__ == "__main__":
    # nosec B104: binding all interfaces is required so the container is
    # reachable from outside; this is not a debug server exposed publicly.
    app.run(host="0.0.0.0", port=5000, debug=False)  # nosec B104
