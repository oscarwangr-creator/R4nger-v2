from __future__ import annotations

from datetime import datetime, timezone
from itertools import count
from typing import Any, Dict

from flask import Flask, Response, jsonify, render_template, request
from flask_cors import CORS

from core.distributed import DistributedExecutor
from core.pipeline_engine import PipelineEngine
from core.security import SecurityManager, require_permission
from core.tool_registry import ToolRegistry
from modules import build_module_registry
from utils.logger import configure_logging


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../web_ui/templates", static_folder="../web_ui/static")
    CORS(app)
    configure_logging()

    security = SecurityManager()
    module_registry = build_module_registry()
    tool_registry = ToolRegistry()
    tool_registry.register_defaults()
    pipeline_engine = PipelineEngine(module_registry=module_registry)
    distributed = DistributedExecutor()

    jobs: Dict[int, Dict[str, Any]] = {}
    job_counter = count(start=1)

    @app.get("/")
    def dashboard():
        return render_template("dashboard.html")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "version": "3.0.0", "tls_min_version": security.tls_min_version})

    @app.post("/api/auth/login")
    def login():
        data = request.get_json(silent=True) or {}
        role = data.get("role", "viewer")
        return jsonify({"token": f"dev-token-{role}", "role": role})

    @app.get("/api/modules")
    @require_permission(security, "read")
    def list_modules():
        return jsonify([{**m.metadata.__dict__} for m in module_registry.values()])

    @app.get("/api/modules/categories")
    @require_permission(security, "read")
    def module_categories():
        categories = sorted({m.metadata.category for m in module_registry.values()})
        return jsonify(categories)

    @app.post("/api/modules/reload")
    @require_permission(security, "manage")
    def reload_modules():
        return jsonify({"status": "reloaded", "count": len(module_registry)})

    @app.get("/api/modules/<name>")
    @require_permission(security, "read")
    def module_info(name: str):
        m = module_registry.get(name)
        if not m:
            return jsonify({"error": "not_found"}), 404
        return jsonify({**m.metadata.__dict__})

    @app.post("/api/modules/<name>/execute")
    @require_permission(security, "execute")
    def execute_module(name: str):
        m = module_registry.get(name)
        if not m:
            return jsonify({"error": "not_found"}), 404
        payload = request.get_json(silent=True) or {}
        job_id = next(job_counter)
        result = m.run(payload)
        jobs[job_id] = {"job_id": job_id, "type": "module", "name": name, "result": result, "created_at": datetime.now(timezone.utc).isoformat()}
        return jsonify(jobs[job_id]), 201

    @app.get("/api/pipelines")
    @require_permission(security, "read")
    def list_pipelines():
        return jsonify(pipeline_engine.list_pipelines())

    @app.get("/api/pipelines/<name>")
    @require_permission(security, "read")
    def pipeline_info(name: str):
        return jsonify(pipeline_engine.load_pipeline(name))

    @app.post("/api/pipelines/<name>/execute")
    @require_permission(security, "execute")
    def execute_pipeline(name: str):
        payload = request.get_json(silent=True) or {}
        parallel = bool(payload.get("parallel", False))
        max_workers = int(payload.get("max_workers", 4))
        job_id = next(job_counter)
        result = pipeline_engine.execute(name=name, payload=payload, parallel=parallel, max_workers=max_workers)
        jobs[job_id] = {"job_id": job_id, "type": "pipeline", "name": name, "result": result, "created_at": datetime.now(timezone.utc).isoformat()}
        return jsonify(jobs[job_id]), 201

    @app.post("/api/pipelines/<name>/validate")
    @require_permission(security, "read")
    def validate_pipeline(name: str):
        data = pipeline_engine.load_pipeline(name)
        missing = [s["module"] for s in data.get("stages", []) if s["module"] not in module_registry]
        return jsonify({"pipeline": name, "valid": not missing, "missing_modules": missing})

    @app.get("/api/jobs")
    @require_permission(security, "read")
    def list_jobs():
        return jsonify(sorted(jobs.values(), key=lambda j: j["job_id"], reverse=True))

    @app.get("/api/jobs/<int:job_id>")
    @require_permission(security, "read")
    def get_job(job_id: int):
        job = jobs.get(job_id)
        if not job:
            return jsonify({"error": "not_found"}), 404
        return jsonify(job)

    @app.get("/api/jobs/<int:job_id>/result")
    @require_permission(security, "read")
    def get_job_result(job_id: int):
        job = jobs.get(job_id)
        if not job:
            return jsonify({"error": "not_found"}), 404
        return jsonify(job["result"])

    @app.delete("/api/jobs/<int:job_id>")
    @require_permission(security, "manage")
    def delete_job(job_id: int):
        if job_id in jobs:
            jobs.pop(job_id)
            return jsonify({"status": "deleted", "job_id": job_id})
        return jsonify({"error": "not_found"}), 404

    @app.get("/api/tools")
    @require_permission(security, "read")
    def tools_status():
        return jsonify(tool_registry.status())

    @app.get("/api/tools/<name>")
    @require_permission(security, "read")
    def tool_info(name: str):
        try:
            return jsonify(tool_registry.get(name))
        except KeyError:
            return jsonify({"error": "not_found"}), 404

    @app.post("/api/workers/register")
    @require_permission(security, "manage")
    def register_worker():
        data = request.get_json(silent=True) or {}
        worker_id = data.get("worker_id")
        capacity = int(data.get("capacity", 2))
        if not worker_id:
            return jsonify({"error": "worker_id required"}), 400
        node = distributed.register_worker(worker_id=worker_id, capacity=capacity)
        return jsonify(node.__dict__), 201

    @app.get("/api/workers")
    @require_permission(security, "read")
    def list_workers():
        return jsonify(distributed.list_workers())

    @app.post("/api/workers/parallel-test")
    @require_permission(security, "execute")
    def workers_parallel_test():
        jobs_in = request.get_json(silent=True) or {}
        targets = jobs_in.get("targets", [])
        task_defs = [lambda t=t: module_registry["nmap_recon"].run({"target": t}) for t in targets]
        return jsonify(distributed.execute_parallel(task_defs, max_workers=min(8, max(1, len(task_defs) or 1))))

    @app.get("/api/reports/formats")
    @require_permission(security, "read")
    def report_formats():
        return jsonify(["html", "json", "pdf"])

    @app.post("/api/reports/generate")
    @require_permission(security, "execute")
    def generate_report():
        data = request.get_json(silent=True) or {}
        fmt = data.get("format", "json")
        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "format": fmt,
            "jobs": len(jobs),
        }
        return jsonify(summary), 201

    @app.get("/api/security/rbac")
    @require_permission(security, "audit")
    def rbac_matrix():
        from core.security import ROLE_MATRIX
        return jsonify({k: sorted(v) for k, v in ROLE_MATRIX.items()})

    @app.get("/api/security/tls")
    @require_permission(security, "read")
    def tls_policy():
        return jsonify({"min_version": security.tls_min_version, "status": "enforced_by_deployment"})

    @app.get("/api/audit/logs")
    @require_permission(security, "audit")
    def audit_logs():
        from pathlib import Path
        p = Path(security.audit_log_path)
        lines = p.read_text().splitlines()[-200:] if p.exists() else []
        return jsonify({"entries": lines})

    @app.get("/api/stream/jobs")
    @require_permission(security, "read")
    def stream_jobs():
        def event_stream() -> str:
            snapshot = sorted(jobs.values(), key=lambda j: j["job_id"], reverse=True)[:20]
            return f"data: {snapshot}\n\n"

        return Response(event_stream(), mimetype="text/event-stream")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
