from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "organization_module"
    category = "organization_intelligence"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'spiderfoot-9 {seed}'
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
                    'toolchain': ['spiderfoot-9', 'shodan-19', 'theharvester-29', 'securitytrails-39', 'spiderfoot-49', 'shodan-59', 'theharvester-69', 'securitytrails-79', 'spiderfoot-89', 'shodan-99', 'theharvester-109', 'securitytrails-119', 'spiderfoot-129', 'shodan-139', 'theharvester-149', 'securitytrails-159', 'spiderfoot-169', 'shodan-179', 'theharvester-189', 'securitytrails-199', 'spiderfoot-209', 'shodan-219', 'theharvester-229', 'securitytrails-239', 'spiderfoot-249', 'shodan-259', 'theharvester-269', 'securitytrails-279', 'spiderfoot-289', 'shodan-299', 'theharvester-309', 'securitytrails-319', 'spiderfoot-329', 'shodan-339', 'theharvester-349', 'securitytrails-359', 'spiderfoot-369', 'shodan-379', 'theharvester-389', 'securitytrails-399', 'spiderfoot-409', 'shodan-419', 'theharvester-429', 'securitytrails-439', 'spiderfoot-449', 'shodan-459', 'theharvester-469', 'securitytrails-479', 'spiderfoot-489', 'shodan-499', 'theharvester-509', 'securitytrails-519'],
                    'pipelines': [],
                    'confidence': 0.7,
                }
            ],
        }
