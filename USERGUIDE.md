# R4nger-V3 User Guide

## 1) Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Start framework

```bash
./start.sh
```

Or run directly:

```bash
python r4ng3r.py api --host 0.0.0.0 --port 5000
```

- API base URL: `http://localhost:5000/api`
- Dashboard: `http://localhost:5000`

## 3) Run modules from CLI

List modules:

```bash
python r4ng3r.py modules list
```

Run a module:

```bash
python r4ng3r.py modules run nmap_recon --target 192.168.1.0/24
```

Run with extra payload:

```bash
python r4ng3r.py modules run shodan_osint --target example.com --payload '{"limit": 25}'
```

## 4) Run pipelines from CLI

List pipelines:

```bash
python r4ng3r.py pipelines list
```

Execute:

```bash
python r4ng3r.py pipelines run osint_intelligence_pipeline --target example.com
python r4ng3r.py pipelines run full_pentest_pipeline --target 10.0.0.0/24 --parallel --max-workers 6
```

## 4.5) Run workflows from CLI

List workflows:

```bash
python r4ng3r.py workflows list
```

Execute:

```bash
python r4ng3r.py workflows run full_assessment_workflow --target example.com
```

## 5) API workflow

### Auth simulation

```bash
curl -s -X POST http://localhost:5000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"role":"admin"}'
```

### Modules

```bash
curl -s http://localhost:5000/api/modules -H 'X-Role: admin'
curl -s -X POST http://localhost:5000/api/modules/spiderfoot_osint/execute \
  -H 'X-Role: admin' -H 'Content-Type: application/json' \
  -d '{"target":"example.com"}'
```

### Pipelines

```bash
curl -s http://localhost:5000/api/pipelines -H 'X-Role: admin'
curl -s -X POST http://localhost:5000/api/pipelines/network_recon_pipeline/execute \
  -H 'X-Role: admin' -H 'Content-Type: application/json' \
  -d '{"target":"192.168.1.0/24","parallel":true,"max_workers":4}'
```

### Workflows

```bash
curl -s http://localhost:5000/api/workflows -H 'X-Role: admin'
curl -s -X POST http://localhost:5000/api/workflows/full_assessment_workflow/execute \
  -H 'X-Role: admin' -H 'Content-Type: application/json' \
  -d '{"target":"example.com"}'
```

### Jobs and reports

```bash
curl -s http://localhost:5000/api/jobs -H 'X-Role: admin'
curl -s -X POST http://localhost:5000/api/reports/generate \
  -H 'X-Role: admin' -H 'Content-Type: application/json' \
  -d '{"format":"json"}'
```

## 6) Security and operations

- Use `X-Role` header for endpoint authorization:
  - `viewer`: read-only
  - `operator`: read + execute
  - `admin`: read + execute + manage + audit
- Read security policy:

```bash
curl -s http://localhost:5000/api/security/rbac -H 'X-Role: admin'
curl -s http://localhost:5000/api/security/tls -H 'X-Role: admin'
curl -s http://localhost:5000/api/config -H 'X-Role: admin'
```

- Read recent audit entries:

```bash
curl -s http://localhost:5000/api/audit/logs -H 'X-Role: admin'
```

## 7) Distributed execution

Register workers and run a parallel validation job:

```bash
curl -s -X POST http://localhost:5000/api/workers/register \
  -H 'X-Role: admin' -H 'Content-Type: application/json' \
  -d '{"worker_id":"worker-1","capacity":4}'

curl -s -X POST http://localhost:5000/api/workers/parallel-test \
  -H 'X-Role: admin' -H 'Content-Type: application/json' \
  -d '{"targets":["10.0.0.1","10.0.0.2"]}'
```

## 8) Troubleshooting

- `403 forbidden`: wrong/missing `X-Role` for endpoint permission
- `Pipeline not found`: verify pipeline name with `python r4ng3r.py pipelines list`
- `missing required input 'target'`: include `--target` or `{"target":"..."}`
- Empty dashboard: confirm API process is running on port `5000`


Note: Job history is persisted in SQLite at `data/r4nger.db` by default.
