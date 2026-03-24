from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "metadata_geolocation_module"
    category = "metadata_geolocation_intelligence"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'creepy {seed}'
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
                    'toolchain': ['creepy', 'exiftool-17', 'foca-27', 'ghunt-37', 'creepy-47', 'exiftool-57', 'foca-67', 'ghunt-77', 'creepy-87', 'exiftool-97', 'foca-107', 'ghunt-117', 'creepy-127', 'exiftool-137', 'foca-147', 'ghunt-157', 'creepy-167', 'exiftool-177', 'foca-187', 'ghunt-197', 'creepy-207', 'exiftool-217', 'foca-227', 'ghunt-237', 'creepy-247', 'exiftool-257', 'foca-267', 'ghunt-277', 'creepy-287', 'exiftool-297', 'foca-307', 'ghunt-317', 'creepy-327', 'exiftool-337', 'foca-347', 'ghunt-357', 'creepy-367', 'exiftool-377', 'foca-387', 'ghunt-397', 'creepy-407', 'exiftool-417', 'foca-427', 'ghunt-437', 'creepy-447', 'exiftool-457', 'foca-467', 'ghunt-477', 'creepy-487', 'exiftool-497', 'foca-507', 'ghunt-517'],
                    'pipelines': [],
                    'confidence': 0.7,
                }
            ],
        }
