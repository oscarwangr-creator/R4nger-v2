from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "social_media_module"
    category = "social_media_intelligence"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'toutatis {seed}'
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
                    'toolchain': ['toutatis', 'tinfoleak-14', 'social-analyzer-24', 'twint-34', 'toutatis-44', 'tinfoleak-54', 'social-analyzer-64', 'twint-74', 'toutatis-84', 'tinfoleak-94', 'social-analyzer-104', 'twint-114', 'toutatis-124', 'tinfoleak-134', 'social-analyzer-144', 'twint-154', 'toutatis-164', 'tinfoleak-174', 'social-analyzer-184', 'twint-194', 'toutatis-204', 'tinfoleak-214', 'social-analyzer-224', 'twint-234', 'toutatis-244', 'tinfoleak-254', 'social-analyzer-264', 'twint-274', 'toutatis-284', 'tinfoleak-294', 'social-analyzer-304', 'twint-314', 'toutatis-324', 'tinfoleak-334', 'social-analyzer-344', 'twint-354', 'toutatis-364', 'tinfoleak-374', 'social-analyzer-384', 'twint-394', 'toutatis-404', 'tinfoleak-414', 'social-analyzer-424', 'twint-434', 'toutatis-444', 'tinfoleak-454', 'social-analyzer-464', 'twint-474', 'toutatis-484', 'tinfoleak-494', 'social-analyzer-504', 'twint-514'],
                    'pipelines': [],
                    'confidence': 0.7,
                }
            ],
        }
