# ⚔ RedTeam Framework v2.0

> **Enterprise-grade modular offensive security platform — Authorized testing only.**  
> Professional/government red team scale with Palantir-level data integration, analytics, and multi-layered investigation capabilities.

---

## Overview

RedTeam Framework (RTF) is a modular operator platform for running offensive security workflows, OSINT/SOCMINT investigations, reporting pipelines, and dashboard/API-driven engagements from one codebase. The project combines:

- **Metasploit-style CLI operations** for day-to-day module execution
- **Workflow orchestration** for repeatable multi-stage engagements
- **API and dashboard surfaces** for automation, observability, and collaboration
- **TITAN / Intelligence OS layers** for distributed investigation and upgrade planning
- **Structured reporting** across HTML, PDF, XLSX, Markdown, and JSON outputs

If you are new to the repo, start with the quick start section below, then use the documentation map to jump to the guide that matches your workflow.

---

## What's new in v2.0

- **23 modules** across 9 categories (recon, osint, AD, cloud, web, crypto, wireless, post-exploitation, network)
- **8 workflows** including `full_ad_compromise`, `identity_fusion`, `ssl_web_recon`, `cloud_audit`
- **Claude AI Stage J** in identity_fusion for intelligent correlation analysis
- **90+ SOCMINT tools** in the 9-stage identity investigation pipeline
- **Metasploit-style console v2** with `setg`, `workspace`, `sessions`, `history/!N`, `grep`, `resource`, `notes`, `creds`, `report`, `spool`
- **Enterprise modules**: Azure AD/Entra, GCP, LDAP, Shodan, SSL/TLS, credential spray, API security
- **Parallel installer v2** with backup commands for 14+ failing tools and exponential backoff
- **Professional reporting engine**: HTML, PDF, XLSX, Markdown, JSON with MITRE ATT&CK mapping

---

## Documentation Map

- **Operator quick reference:** `README.md`
- **Full operator manual:** `rtf/USER_GUIDE.md`
- **SOCMINT investigation playbook:** `rtf/SOCMINT_IDENTITY_OPERATIONS_GUIDE.md`
- **Dashboard UI notes:** `rtf/dashboard_ui/README.md`
- **Upgrade artifacts:** `rtf/V4_ARCHITECTURE_REPORT.md`, `rtf/V4_UPGRADE_REPORT.json`
- **Codex planning pack:** `rtf/intelligence_os/planning/CODEX_AUTHORIZED_UPGRADE_BRIEF.md`, `rtf/intelligence_os/planning/workflow_mappings.yaml`, `rtf/intelligence_os/planning/example_investigations.yaml`

Recommended reading order for new users:

1. Read **Quick Start** in this README.
2. Open **`rtf/USER_GUIDE.md`** for installation, console, workflow, API, and reporting details.
3. Open **`rtf/SOCMINT_IDENTITY_OPERATIONS_GUIDE.md`** before running identity investigations.
4. Review TITAN / upgrade sections if you plan to use the distributed architecture layers.

---

## Quick Start

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the interactive console (Metasploit-style)
python rtf.py console

# Run a module directly
python rtf.py module run recon/subdomain_enum --options '{"target":"example.com"}'

# Run the full installer
python rtf.py install

# Start the REST API
python rtf.py api --port 8000

# Start the web dashboard
python rtf.py dashboard --port 5000

# Generate the V4 architecture report
python rtf.py upgrade analyze

# Regenerate the Codex planning pack
python rtf/intelligence_os/scripts/generate_upgrade_pack.py

# Docker
docker compose up -d
```

### Suggested first-run checklist

1. Install Python requirements.
2. Run `python rtf.py install` or a category-scoped install.
3. Verify tool availability with `python rtf.py tools summary`.
4. Launch the console and validate module loading with `show modules`.
5. Start the API/dashboard only after the local CLI path is working.
6. Create a dedicated workspace before storing findings, notes, or credentials.

---

## Common operator workflows

### 1. Interactive console workflow

```text
rtf > workspace client-acme
rtf > use recon/subdomain_enum
rtf > set target example.com
rtf > run
rtf > use web/api_security
rtf > set url https://api.example.com
rtf > run
rtf > report html reports/client-acme.html
```

### 2. Direct module execution

```bash
python rtf.py module run recon/ssl_scan --options '{"target":"example.com"}'
python rtf.py module run web/api_security --options '{"url":"https://api.example.com"}'
python rtf.py module run cloud/aws_enum --options '{"profile":"default"}'
```

### 3. Workflow execution

```bash
python rtf.py workflow list
python rtf.py workflow run full_recon --options '{"target":"example.com"}'
python rtf.py workflow run identity_fusion --options '{"username":"target_handle","output_format":"html"}'
```

### 4. API and dashboard operations

```bash
python rtf.py api --host 0.0.0.0 --port 8000
python rtf.py dashboard --host 127.0.0.1 --port 5000
```

---

## Console Commands

```
rtf > use recon/subdomain_enum        # Select a module
rtf > set target example.com          # Set option
rtf > setg domain example.com         # Set GLOBAL option (persists)
rtf > show options                    # Show current options
rtf > run                             # Execute module
rtf > back                            # Deselect module

rtf > search subdomain                # Search modules
rtf > info recon/port_scan            # Module details
rtf > workflows                       # List all 8 workflows
rtf > run_workflow full_recon {"target":"example.com"}

rtf > workspace pentest-corp          # Switch workspace
rtf > notes example.com "Admin panel found at /admin"
rtf > report html reports/engagement.html
rtf > spool logs/session.log          # Log everything to file

rtf > history                         # Command history
rtf > !5                              # Replay command #5
rtf > grep admin search web           # Filter output by regex

rtf > jobs                            # Recent jobs
rtf > findings --severity high        # Filter findings
rtf > db_status                       # Database status
```

---

## Modules (23 total)

| Category | Module | Description |
|----------|--------|-------------|
| recon | subdomain_enum | subfinder + assetfinder + httpx |
| recon | port_scan | naabu + nmap service detection |
| recon | nuclei_scan | Template-based vulnerability scanner |
| recon | ssl_scan | TLS/SSL certificate + protocol analysis |
| recon | shodan_search | Shodan host/search/CVE enumeration |
| osint | username_enum | Sherlock 300+ social networks |
| osint | email_harvest | theHarvester multi-source |
| osint | identity_fusion | **9-stage SOCMINT, 90+ tools, Claude AI** |
| active_directory | bloodhound_collect | BloodHound Python ingestor |
| active_directory | kerberoast | Impacket TGS ticket extraction |
| active_directory | asreproast | AS-REP hash capture |
| cloud | aws_enum | boto3 IAM/S3/EC2/Lambda |
| cloud | azure_enum | Azure AD/Entra ID enumeration |
| cloud | gcp_enum | GCP IAM/Storage/Compute |
| network | ldap_enum | AD LDAP: users, admins, policy, GPOs |
| web | dir_fuzz | ffuf directory/file fuzzing |
| web | xss_scan | dalfox XSS scanner |
| web | sqli_scan | sqlmap automation |
| web | api_security | Security headers, GraphQL, Swagger |
| crypto | hash_crack | hashcat GPU/CPU cracking |
| wireless | wpa2_capture | aircrack-ng WPA2 handshake |
| post_exploitation | privesc_check | SUID/sudo/cron/caps + LinPEAS |
| post_exploitation | credential_spray | Low-and-slow spray: SMB/WinRM/LDAP |

---

## Identity Fusion Pipeline (osint/identity_fusion)

9-stage investigation with 90+ tools and Claude AI correlation:

```
Stage A  Seed normalization
Stage B  Username sweep      (sherlock, maigret, nexfil, blackbird, socialscan + 12 more)
Stage C  Email pivot/breach  (holehe, h8mail, emailrep, dehashed + 5 more)
Stage D  Social media        (instaloader, twint, toutatis, osintgram + 5 more)
Stage E  Domain intel        (theHarvester, spiderfoot, shodan, censys + 16 more)
Stage F  Code/secrets        (gitfive, trufflehog, gitleaks + 4 more)
Stage G  Phone OSINT         (phoneinfoga, email2phonenumber)
Stage H  Dark web/breach     (intelx, pwndb-cli, dehashed + 2 more)
Stage I  Geo/metadata        (creepy, waybackpack, ghunt, exiftool + 16 more)
Stage J  Claude AI correlation & confidence scoring
Stage K  Multi-format report  JSON / CSV / XLSX / PDF / HTML
```

```bash
python rtf.py module run osint/identity_fusion   --options '{"username":"target_handle","email":"target@example.com","output_format":"html","use_ai":true}'
```

For deeper operating guidance, pivot logic, and example playbooks, see `rtf/SOCMINT_IDENTITY_OPERATIONS_GUIDE.md`.

---

## Workflows (8 built-in)

```
full_recon         subdomain_enum → port_scan → nuclei_scan
ad_attack          bloodhound_collect → kerberoast → asreproast
web_audit          dir_fuzz → xss_scan → sqli_scan → api_security
osint_person       username_enum → email_harvest
identity_fusion    Full 9-stage SOCMINT pipeline
cloud_audit        aws_enum → shodan_search
full_ad_compromise ldap_enum → bloodhound → kerberoast → asreproast
ssl_web_recon      ssl_scan → subdomain_enum → nuclei → api_security
```

Use workflows when you need repeatability, reporting continuity, and lower operator overhead across common engagement patterns.

---

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/stats` | System stats |
| GET | `/modules` | List all modules |
| POST | `/modules/{cat}/{name}/run` | Execute a module |
| GET | `/workflows` | List workflows |
| POST | `/workflows/{name}/run` | Run a workflow |
| GET | `/jobs` | List jobs (paginated) |
| GET | `/findings` | List findings (paginated) |
| GET | `/tools/summary` | Tool installation summary |

All endpoints also under `/api/v1/...` for versioned access.

---

## Dashboard, TITAN, and upgrade surfaces

### Web dashboard

Use the dashboard for high-level metrics, job history, findings review, and workflow launches:

```bash
python rtf.py dashboard --port 5000
```

### TITAN architecture layer

RTF v2.4 includes a backward-compatible TITAN architecture layer for distributed OSINT, SOCMINT, CASM, credential intelligence, graph analytics, AI identity resolution, queue-backed orchestration, and multi-service observability.

Useful commands:

```bash
python rtf.py titan manifest
python rtf.py titan health
python rtf.py titan investigate --options '{"username":"target_handle"}'
```

### V4 Upgrade Pipeline

RTF v4.0 exposes a sequential upgrade pipeline that preserves CLI and module compatibility while generating machine-readable architecture artifacts.

```bash
python rtf.py upgrade analyze   # architecture map + report artifacts
python rtf.py upgrade run       # full sequential agent output
```

The pipeline executes these agents in order:

1. Architecture agent
2. Module builder
3. OSINT pipeline builder
4. SOCMINT pipeline builder
5. Dashboard builder
6. Self-healing system builder
7. Final integration engine

Artifacts are written to `rtf/V4_ARCHITECTURE_REPORT.md` and `rtf/V4_UPGRADE_REPORT.json`.

The Intelligence OS expansion layer now also ships a generated manifest and installer bootstrap with 520 mapped tools, 60+ advanced pipelines, and workflow metadata under `rtf/intelligence_os/manifests`, `rtf/intelligence_os/pipelines`, and `rtf/intelligence_os/install`.

---

## Safety, authorization, and scope

For **authorized testing only**: penetration testing engagements, red team operations with written permission, CTF competitions, and internal security research in controlled lab environments.

Recommended operator controls:

- Create a fresh workspace per client or scenario.
- Store API keys and secrets in config or environment variables rather than shell history.
- Validate third-party tool licensing and local policy requirements before installation.
- Keep generated findings, reports, and loot under engagement-specific directories.
- Review report output before sharing externally.

---

## Where to go next

- Want end-to-end usage details? Read `rtf/USER_GUIDE.md`.
- Running identity investigations? Read `rtf/SOCMINT_IDENTITY_OPERATIONS_GUIDE.md`.
- Working on the frontend dashboard? Read `rtf/dashboard_ui/README.md`.

![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/oscarvandeijk-coder/r4ng3r-V2?utm_source=oss&utm_medium=github&utm_campaign=oscarvandeijk-coder%2Fr4ng3r-V2&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)
