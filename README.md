# R4nger-V3

R4nger-V3 is a modular security orchestration framework for **authorized** OSINT, recon, exploitation simulation, post-exploitation simulation, and reporting.

## What is included

- Clean V3 structure: `core`, `modules`, `pipelines`, `api`, `web_ui`, `tools`, `utils`
- 24 built-in modules across OSINT, Recon, Exploit, Post-Exploit, and Reporting
- 6 production pipelines:
  - `osint_intelligence_pipeline`
  - `network_recon_pipeline`
  - `vuln_scan_pipeline`
  - `exploit_pipeline`
  - `post_exploit_pipeline`
  - `full_pentest_pipeline`
- Flask REST API (20+ endpoints) for modules, pipelines, jobs, workers, tools, reports, and security/audit operations
- Web dashboard with real-time status refresh
- Distributed execution primitives, RBAC enforcement, TLS 1.3 policy metadata, and audit logging

## Quick start (local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./start.sh
```

Open `http://localhost:5000`.

## One obvious entrypoint

Use `r4ng3r.py` for all framework operations:

```bash
# Start API + dashboard
python r4ng3r.py api --port 5000

# List modules
python r4ng3r.py modules list

# Run a module
python r4ng3r.py modules run spiderfoot_osint --target example.com

# List pipelines
python r4ng3r.py pipelines list

# Run a pipeline
python r4ng3r.py pipelines run full_pentest_pipeline --target 10.10.10.0/24
```

## Security defaults

- RBAC permissions enforced per endpoint via `X-Role` header (`viewer`, `operator`, `admin`)
- TLS minimum policy is `TLSv1.3` (terminate TLS at deployment edge)
- Audit log written to `logs/audit.log`

## Authorized use only

Run this framework only with written authorization and a defined testing scope.
