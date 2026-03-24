from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "ghunt_module"
    category = "generated"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'ghunt {seed}'
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
                    'toolchain': ['ghunt'],
                    'pipelines': ['metadata_intelligence_pipeline', 'geolocation_pivot_pipeline', 'executive_watch_pipeline', 'subsidiary_mapping_pipeline', 'facility_mapping_pipeline', 'academic_research_pipeline', 'ngo_partnership_pipeline'],
                    'confidence': 0.7,
                }
            ],
        }
