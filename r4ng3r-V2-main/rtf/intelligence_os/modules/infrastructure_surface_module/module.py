from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "infrastructure_surface_module"
    category = "infrastructure_attack_surface"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'nmap-10 {seed}'
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
                    'toolchain': ['nmap-10', 'httpx-20', 'whatweb-30', 'aquatone-40', 'nmap-50', 'httpx-60', 'whatweb-70', 'aquatone-80', 'nmap-90', 'httpx-100', 'whatweb-110', 'aquatone-120', 'nmap-130', 'httpx-140', 'whatweb-150', 'aquatone-160', 'nmap-170', 'httpx-180', 'whatweb-190', 'aquatone-200', 'nmap-210', 'httpx-220', 'whatweb-230', 'aquatone-240', 'nmap-250', 'httpx-260', 'whatweb-270', 'aquatone-280', 'nmap-290', 'httpx-300', 'whatweb-310', 'aquatone-320', 'nmap-330', 'httpx-340', 'whatweb-350', 'aquatone-360', 'nmap-370', 'httpx-380', 'whatweb-390', 'aquatone-400', 'nmap-410', 'httpx-420', 'whatweb-430', 'aquatone-440', 'nmap-450', 'httpx-460', 'whatweb-470', 'aquatone-480', 'nmap-490', 'httpx-500', 'whatweb-510', 'aquatone-520'],
                    'pipelines': [],
                    'confidence': 0.7,
                }
            ],
        }
