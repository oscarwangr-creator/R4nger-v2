# RTF Intelligence Dashboard UI

Production-oriented React + TypeScript control surface for the RedTeam Framework.

## Features

- Operation command center with live framework metrics.
- Graph intelligence view backed by the framework entity and relationship schema.
- Module control center using the real module loader registry.
- Workflow builder panel for the built-in workflow DAGs.
- SOCMINT investigation panel wired to the TITAN 15-stage pipeline.
- Terminal, event stream, reporting, vault, and system health views.

## Run

```bash
cd rtf/dashboard_ui
npm install
npm run build
```

Then start the FastAPI server from the framework root:

```bash
cd rtf
python -m framework.api.server
```

Open `http://127.0.0.1:8000/dashboard`.

## API assumptions

The frontend expects the FastAPI server to expose the dashboard endpoints added in `framework/api/server.py` and a websocket event stream at `/ws/events`.
