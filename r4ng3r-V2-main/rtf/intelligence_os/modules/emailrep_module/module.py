from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "emailrep_module"
    category = "generated"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'emailrep {seed}'
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
                    'toolchain': ['emailrep'],
                    'pipelines': ['email_intelligence_pipeline', 'paste_monitoring_pipeline', 'mobile_app_intelligence_pipeline', 'messaging_app_pipeline', 'conference_exposure_pipeline'],
                    'confidence': 0.7,
                }
            ],
        }
