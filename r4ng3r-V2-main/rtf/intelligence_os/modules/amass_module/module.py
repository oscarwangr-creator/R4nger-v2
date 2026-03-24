from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "amass_module"
    category = "generated"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'amass {seed}'
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
                    'toolchain': ['amass'],
                    'pipelines': ['identity_mega_pipeline', 'domain_infrastructure_pipeline', 'organization_profiling_pipeline', 'executive_watch_pipeline', 'brand_impersonation_pipeline', 'newsletter_leak_pipeline', 'persona_correlation_pipeline', 'public_records_pipeline', 'asset_ownership_pipeline'],
                    'confidence': 0.7,
                }
            ],
        }
