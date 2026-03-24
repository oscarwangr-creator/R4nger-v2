#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$ROOT_DIR/install/tool_installer.py"
python3 "$ROOT_DIR/install/database_setup.py"
echo "Intelligence OS install bootstrap completed."
