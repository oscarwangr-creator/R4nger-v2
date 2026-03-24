from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "spiderfoot_module"
    category = "generated"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'spiderfoot {seed}'
    entity_map = {'seed': 'Artifact'}

    def run(self, input_data, context=None):
        seed_value = next(iter(input_data.values()), 'seed')
        return {
            'input': input_data,
            'command': self.build_command({'seed': seed_value}),
            'artifacts': [
                {
                    'seed': seed_value,
                    'module': self.name,
                    'category': self.category,
                    'toolchain': ['spiderfoot'],
                    'pipelines': ['organization_profiling_pipeline', 'fraud_investigation_pipeline', 'marketing_asset_pipeline', 'disinformation_monitoring_pipeline', 'subsidiary_domain_pipeline'],
                    'confidence': 0.7,
                }
            ],
        }
