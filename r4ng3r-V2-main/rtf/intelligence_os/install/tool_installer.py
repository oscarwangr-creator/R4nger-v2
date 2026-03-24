from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

def main() -> None:
    manifest = Path(__file__).resolve().parents[1] / 'manifests' / 'framework_manifest.json'
    data = json.loads(manifest.read_text())
    counts = Counter(tool['install_method'] for tool in data['tools'])
    print('Planned tool installation batches:')
    for method, count in sorted(counts.items()):
        print(f' - {method}: {count} tools')

if __name__ == '__main__':
    main()
