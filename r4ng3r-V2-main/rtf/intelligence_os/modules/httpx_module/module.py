from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "httpx_module"
    category = "generated"
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
                    'toolchain': ['httpx'],
                    'pipelines': ['domain_infrastructure_pipeline', 'infrastructure_exposure_pipeline', 'brand_impersonation_pipeline', 'vendor_attack_surface_pipeline', 'newsletter_leak_pipeline', 'crypto_wallet_pipeline', 'persona_correlation_pipeline', 'chat_server_pipeline', 'public_records_pipeline', 'malware_repo_pipeline', 'asset_ownership_pipeline', 'dataset_leak_pipeline'],
                    'confidence': 0.7,
                }
            ],
        }
