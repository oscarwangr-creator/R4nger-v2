from __future__ import annotations

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestExternalToolModules(unittest.TestCase):
    def setUp(self):
        from framework.modules.loader import ModuleLoader
        self.loader = ModuleLoader()
        self.loader.load_all()

    def test_requested_modules_are_registered(self):
        expected = {
            'osint/sherlock', 'osint/maigret', 'osint/nexfil', 'osint/blackbird', 'osint/social_analyzer',
            'osint/whatsmyname', 'osint/checkusernames', 'osint/namechk', 'osint/twint', 'osint/instaloader',
            'osint/snscrape', 'osint/toutatis', 'osint/gitfive', 'osint/reddit_user_analyser', 'osint/google',
            'osint/duckduckgo', 'osint/bing', 'osint/brave', 'osint/yahoo', 'osint/startpage', 'osint/qwant',
            'osint/swisscows', 'osint/yandex', 'osint/baidu', 'recon/subfinder', 'recon/amass', 'recon/httpx',
            'recon/naabu', 'recon/nmap', 'recon/nuclei', 'osint/trufflehog', 'osint/gitleaks', 'osint/exiftool',
        }
        self.assertTrue(expected.issubset(set(self.loader._registry)))

    def test_module_builds_structured_command(self):
        cls = self.loader.get('recon/nuclei')
        module = cls()
        module.set_options({'target': 'https://example.com', 'output_file': '/tmp/out.json'})
        command, temp_output = module.build_command('https://example.com', '/tmp/out.json')
        self.assertIn('-json-export', command)
        self.assertIsNone(temp_output)

    def test_search_parser_returns_dicts(self):
        cls = self.loader.get('osint/google')
        module = cls()
        parsed = module.parse_output('Example Result - https://example.com\nAnother Result | https://example.org')
        self.assertEqual(parsed[0]['rank'], 1)
        self.assertEqual(parsed[0]['url'], 'https://example.com')
        self.assertEqual(parsed[1]['url'], 'https://example.org')


class TestOSINTToolkitWorkflow(unittest.TestCase):
    def test_builtin_workflow_registered(self):
        from framework.workflows.engine import BUILTIN_WORKFLOWS, get_workflow
        self.assertIn('osint_toolkit', BUILTIN_WORKFLOWS)
        workflow = get_workflow('osint_toolkit', {'username': 'alice', 'domain': 'example.com'})
        self.assertEqual(workflow.name, 'osint_toolkit')


if __name__ == '__main__':
    unittest.main(verbosity=2)
