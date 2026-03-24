#!/usr/bin/env bash
set -euo pipefail

uvicorn intelligence_os.api.app:create_app --factory --host 0.0.0.0 --port 8010
