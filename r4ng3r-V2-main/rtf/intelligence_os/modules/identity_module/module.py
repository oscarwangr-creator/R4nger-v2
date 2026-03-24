from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "identity_module"
    category = "identity_intelligence"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'sherlock {seed}'
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
                    'toolchain': ['sherlock', 'blackbird-11', 'whatsmyname-21', 'userrecon-31', 'sherlock-41', 'blackbird-51', 'whatsmyname-61', 'userrecon-71', 'sherlock-81', 'blackbird-91', 'whatsmyname-101', 'userrecon-111', 'sherlock-121', 'blackbird-131', 'whatsmyname-141', 'userrecon-151', 'sherlock-161', 'blackbird-171', 'whatsmyname-181', 'userrecon-191', 'sherlock-201', 'blackbird-211', 'whatsmyname-221', 'userrecon-231', 'sherlock-241', 'blackbird-251', 'whatsmyname-261', 'userrecon-271', 'sherlock-281', 'blackbird-291', 'whatsmyname-301', 'userrecon-311', 'sherlock-321', 'blackbird-331', 'whatsmyname-341', 'userrecon-351', 'sherlock-361', 'blackbird-371', 'whatsmyname-381', 'userrecon-391', 'sherlock-401', 'blackbird-411', 'whatsmyname-421', 'userrecon-431', 'sherlock-441', 'blackbird-451', 'whatsmyname-461', 'userrecon-471', 'sherlock-481', 'blackbird-491', 'whatsmyname-501', 'userrecon-511'],
                    'pipelines': [],
                    'confidence': 0.7,
                }
            ],
        }
