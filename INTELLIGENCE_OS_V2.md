# Intelligence OS v2

Production-grade additive architecture introducing:

- Modular backend (`core_v2`, `ai_v2`, `graph_v2`, `distributed_v2`, `api_v2`).
- Tool system with auto-discovery and standardized contracts in `BaseTool`.
- 25 fully implemented tools across 16 categories with scalable pattern to 500+ tools.
- 21 YAML pipelines and 3 workflow definitions.
- Autonomous expansion and pentesting engines.
- FastAPI API and WebSocket realtime channel.
- Celery + Redis distributed execution.
- React + TypeScript + Tailwind dashboard with graph and risk analytics.
- Dockerized services and Kubernetes manifests with HPA and cloud agents.

Run local stack:

```bash
docker compose up --build
```

API:

- `POST /pipeline/run`
- `POST /pipeline/async`
- `POST /workflow/run`
- `GET /tools`
- `POST /graph/query`

