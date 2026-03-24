from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import yaml

from intelligence_os.tooling.catalog import load_framework_manifest

ROOT = Path(__file__).resolve().parents[1]
MODULE_ROOT = ROOT / 'modules'
MANIFEST = load_framework_manifest()


def slug_to_title(value: str) -> str:
    return value.replace('_', ' ').replace('-', ' ').title()


def build_module_py(module: dict) -> str:
    primary_tool = module.get('tools', ['seed-normalizer'])[0]
    pipelines = module.get('pipelines', [])
    return dedent(
        f'''
        from __future__ import annotations

        from intelligence_os.tooling.base import JsonEntityModule


        class GeneratedModule(JsonEntityModule):
            name = "{module['name']}"
            category = "{module['category']}"
            input_types = ['seed']
            output_types = ['artifact']
            command_template = '{primary_tool} {{seed}}'
            entity_map = {{'seed': 'Artifact'}}

            def run(self, input_data, context=None):
                seed_value = next(iter(input_data.values()), 'seed')
                return {{
                    'input': input_data,
                    'command': self.build_command({{'seed': seed_value}}),
                    'artifacts': [
                        {{
                            'seed': seed_value,
                            'module': self.name,
                            'category': self.category,
                            'toolchain': {module.get('tools', [])!r},
                            'pipelines': {pipelines!r},
                            'confidence': 0.7,
                        }}
                    ],
                }}
        '''
    ).lstrip()


def build_config_yaml(module: dict) -> str:
    payload = {
        'name': module['name'],
        'category': module['category'],
        'tools': module.get('tools', []),
        'pipelines': module.get('pipelines', []),
        'timeouts': {'execution_seconds': 120, 'api_seconds': 30},
        'rate_limits': {'requests_per_minute': 30, 'burst': 5},
        'reporting': {'formats': ['json', 'csv', 'xlsx', 'pdf', 'html', 'mtgl']},
    }
    return yaml.safe_dump(payload, sort_keys=False)


def build_requirements_txt() -> str:
    return 'PyYAML>=6.0\n'


def build_readme(module: dict) -> str:
    return dedent(
        f'''
        # {slug_to_title(module['name'])}

        - **Category:** {module['category']}
        - **Tools:** {', '.join(module.get('tools', []))}
        - **Pipelines:** {', '.join(module.get('pipelines', []))}

        ## Purpose
        Standardized Intelligence OS module pack generated from the canonical framework manifest.

        ## Accepted Seeds
        Arbitrary seed dictionaries; wrappers normalize them into the shared execution contract.

        ## Output Schema
        Returns normalized artifacts, entities, relationships, and telemetry for downstream graph and reporting stages.
        '''
    ).lstrip()


def sync_module_packs() -> int:
    MODULE_ROOT.mkdir(parents=True, exist_ok=True)
    count = 0
    for module in MANIFEST.get('modules', []):
        target = MODULE_ROOT / module['name']
        target.mkdir(parents=True, exist_ok=True)
        (target / 'module.py').write_text(build_module_py(module))
        (target / 'config.yaml').write_text(build_config_yaml(module))
        (target / 'requirements.txt').write_text(build_requirements_txt())
        (target / 'README.md').write_text(build_readme(module))
        count += 1
    return count


if __name__ == '__main__':
    generated = sync_module_packs()
    print(f'Generated {generated} module packs in {MODULE_ROOT}')
