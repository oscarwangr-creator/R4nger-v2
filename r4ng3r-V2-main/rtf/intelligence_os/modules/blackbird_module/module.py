from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "blackbird_module"
    category = "generated"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'blackbird {seed}'
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
                    'toolchain': ['blackbird'],
                    'pipelines': ['username_intelligence_pipeline', 'forum_monitoring_pipeline', 'package_registry_pipeline', 'video_intelligence_pipeline', 'startup_due_diligence_pipeline'],
                    'confidence': 0.7,
                }
            ],
        }
