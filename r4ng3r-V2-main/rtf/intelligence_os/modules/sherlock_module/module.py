from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "sherlock_module"
    category = "generated"
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
                    'toolchain': ['sherlock'],
                    'pipelines': ['identity_mega_pipeline', 'username_intelligence_pipeline', 'account_verification_pipeline', 'executive_watch_pipeline', 'brand_impersonation_pipeline', 'threat_actor_profiling_pipeline', 'employee_enumeration_pipeline', 'forum_monitoring_pipeline', 'package_registry_pipeline', 'video_intelligence_pipeline', 'startup_due_diligence_pipeline'],
                    'confidence': 0.7,
                }
            ],
        }
