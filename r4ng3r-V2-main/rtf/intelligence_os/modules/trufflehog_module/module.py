from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "trufflehog_module"
    category = "generated"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'trufflehog {seed}'
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
                    'toolchain': ['trufflehog'],
                    'pipelines': ['github_secrets_pipeline', 'code_contributor_pipeline', 'supply_chain_risk_pipeline', 'credential_reuse_pipeline', 'recruitment_signal_pipeline', 'press_correlation_pipeline', 'influencer_mapping_pipeline', 'board_member_pipeline'],
                    'confidence': 0.7,
                }
            ],
        }
