from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "domain_infrastructure_module"
    category = "domain_infrastructure_intelligence"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'httpx {seed}'
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
                    'toolchain': ['httpx', 'sublist3r-15', 'amass-25', 'assetfinder-35', 'httpx-45', 'sublist3r-55', 'amass-65', 'assetfinder-75', 'httpx-85', 'sublist3r-95', 'amass-105', 'assetfinder-115', 'httpx-125', 'sublist3r-135', 'amass-145', 'assetfinder-155', 'httpx-165', 'sublist3r-175', 'amass-185', 'assetfinder-195', 'httpx-205', 'sublist3r-215', 'amass-225', 'assetfinder-235', 'httpx-245', 'sublist3r-255', 'amass-265', 'assetfinder-275', 'httpx-285', 'sublist3r-295', 'amass-305', 'assetfinder-315', 'httpx-325', 'sublist3r-335', 'amass-345', 'assetfinder-355', 'httpx-365', 'sublist3r-375', 'amass-385', 'assetfinder-395', 'httpx-405', 'sublist3r-415', 'amass-425', 'assetfinder-435', 'httpx-445', 'sublist3r-455', 'amass-465', 'assetfinder-475', 'httpx-485', 'sublist3r-495', 'amass-505', 'assetfinder-515'],
                    'pipelines': [],
                    'confidence': 0.7,
                }
            ],
        }
