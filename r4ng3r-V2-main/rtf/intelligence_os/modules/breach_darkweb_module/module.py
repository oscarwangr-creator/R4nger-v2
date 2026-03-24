from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "breach_darkweb_module"
    category = "breach_darkweb_intelligence"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'ahmia {seed}'
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
                    'toolchain': ['ahmia', 'breachdirectory-16', 'dehashed-26', 'intelx-36', 'ahmia-46', 'breachdirectory-56', 'dehashed-66', 'intelx-76', 'ahmia-86', 'breachdirectory-96', 'dehashed-106', 'intelx-116', 'ahmia-126', 'breachdirectory-136', 'dehashed-146', 'intelx-156', 'ahmia-166', 'breachdirectory-176', 'dehashed-186', 'intelx-196', 'ahmia-206', 'breachdirectory-216', 'dehashed-226', 'intelx-236', 'ahmia-246', 'breachdirectory-256', 'dehashed-266', 'intelx-276', 'ahmia-286', 'breachdirectory-296', 'dehashed-306', 'intelx-316', 'ahmia-326', 'breachdirectory-336', 'dehashed-346', 'intelx-356', 'ahmia-366', 'breachdirectory-376', 'dehashed-386', 'intelx-396', 'ahmia-406', 'breachdirectory-416', 'dehashed-426', 'intelx-436', 'ahmia-446', 'breachdirectory-456', 'dehashed-466', 'intelx-476', 'ahmia-486', 'breachdirectory-496', 'dehashed-506', 'intelx-516'],
                    'pipelines': [],
                    'confidence': 0.7,
                }
            ],
        }
