from __future__ import annotations
import json
from pathlib import Path

def main() -> None:
    manifest = Path(__file__).resolve().parents[1] / 'manifests' / 'framework_manifest.json'
    data = json.loads(manifest.read_text())
    print(f"tools={len(data['tools'])} modules={len(data['modules'])} pipelines={len(data['pipelines'])} workflows={len(data['workflows'])}")

if __name__ == '__main__':
    main()
