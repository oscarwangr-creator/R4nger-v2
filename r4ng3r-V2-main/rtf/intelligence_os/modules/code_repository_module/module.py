from __future__ import annotations

from intelligence_os.tooling.base import JsonEntityModule


class GeneratedModule(JsonEntityModule):
    name = "code_repository_module"
    category = "code_repository_intelligence"
    input_types = ['seed']
    output_types = ['artifact']
    command_template = 'ripgrep {seed}'
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
                    'toolchain': ['ripgrep', 'trufflehog-18', 'github-search-28', 'repo-supervisor-38', 'ripgrep-48', 'trufflehog-58', 'github-search-68', 'repo-supervisor-78', 'ripgrep-88', 'trufflehog-98', 'github-search-108', 'repo-supervisor-118', 'ripgrep-128', 'trufflehog-138', 'github-search-148', 'repo-supervisor-158', 'ripgrep-168', 'trufflehog-178', 'github-search-188', 'repo-supervisor-198', 'ripgrep-208', 'trufflehog-218', 'github-search-228', 'repo-supervisor-238', 'ripgrep-248', 'trufflehog-258', 'github-search-268', 'repo-supervisor-278', 'ripgrep-288', 'trufflehog-298', 'github-search-308', 'repo-supervisor-318', 'ripgrep-328', 'trufflehog-338', 'github-search-348', 'repo-supervisor-358', 'ripgrep-368', 'trufflehog-378', 'github-search-388', 'repo-supervisor-398', 'ripgrep-408', 'trufflehog-418', 'github-search-428', 'repo-supervisor-438', 'ripgrep-448', 'trufflehog-458', 'github-search-468', 'repo-supervisor-478', 'ripgrep-488', 'trufflehog-498', 'github-search-508', 'repo-supervisor-518'],
                    'pipelines': [],
                    'confidence': 0.7,
                }
            ],
        }
