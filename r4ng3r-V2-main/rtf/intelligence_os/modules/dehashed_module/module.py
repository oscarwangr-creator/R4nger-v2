from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "dehashed_module"
    category = "generated"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'dehashed {seed}'
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
                    'toolchain': ['dehashed'],
                    'pipelines': ['identity_mega_pipeline', 'email_intelligence_pipeline', 'dark_web_exposure_pipeline', 'breach_correlation_pipeline', 'executive_watch_pipeline', 'supply_chain_risk_pipeline', 'credential_reuse_pipeline', 'vendor_attack_surface_pipeline', 'paste_monitoring_pipeline', 'typosquat_monitoring_pipeline', 'mobile_app_intelligence_pipeline', 'event_monitoring_pipeline', 'messaging_app_pipeline', 'ngo_network_pipeline', 'conference_exposure_pipeline', 'campaign_tracking_pipeline'],
                    'confidence': 0.7,
                }
            ],
        }
