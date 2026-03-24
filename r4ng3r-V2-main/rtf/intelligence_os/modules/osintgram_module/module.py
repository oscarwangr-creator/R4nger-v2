from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "osintgram_module"
    category = "generated"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'osintgram {seed}'
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
                    'toolchain': ['osintgram'],
                    'pipelines': ['image_recon_pipeline', 'vulnerability_trend_pipeline', 'ransomware_exposure_pipeline', 'pastebin_identity_pipeline'],
                    'confidence': 0.7,
                }
            ],
        }
