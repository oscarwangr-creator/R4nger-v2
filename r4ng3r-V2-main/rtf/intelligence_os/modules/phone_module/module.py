from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "phone_module"
    category = "phone_intelligence"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'whocalld {seed}'
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
                    'toolchain': ['whocalld', 'osintcombine-13', 'signalhire-23', 'phoneinfoga-33', 'whocalld-43', 'osintcombine-53', 'signalhire-63', 'phoneinfoga-73', 'whocalld-83', 'osintcombine-93', 'signalhire-103', 'phoneinfoga-113', 'whocalld-123', 'osintcombine-133', 'signalhire-143', 'phoneinfoga-153', 'whocalld-163', 'osintcombine-173', 'signalhire-183', 'phoneinfoga-193', 'whocalld-203', 'osintcombine-213', 'signalhire-223', 'phoneinfoga-233', 'whocalld-243', 'osintcombine-253', 'signalhire-263', 'phoneinfoga-273', 'whocalld-283', 'osintcombine-293', 'signalhire-303', 'phoneinfoga-313', 'whocalld-323', 'osintcombine-333', 'signalhire-343', 'phoneinfoga-353', 'whocalld-363', 'osintcombine-373', 'signalhire-383', 'phoneinfoga-393', 'whocalld-403', 'osintcombine-413', 'signalhire-423', 'phoneinfoga-433', 'whocalld-443', 'osintcombine-453', 'signalhire-463', 'phoneinfoga-473', 'whocalld-483', 'osintcombine-493', 'signalhire-503', 'phoneinfoga-513'],
                    'pipelines': [],
                    'confidence': 0.7,
                }
            ],
        }
