from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "wafw00f_module"
    category = "generated"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'wafw00f {seed}'
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
                    'toolchain': ['wafw00f'],
                    'pipelines': ['infrastructure_exposure_pipeline'],
                    'confidence': 0.7,
                }
            ],
        }
