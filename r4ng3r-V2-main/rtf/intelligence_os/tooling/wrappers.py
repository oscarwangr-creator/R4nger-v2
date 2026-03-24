from __future__ import annotations
from typing import Dict

from intelligence_os.tooling.base import JsonEntityModule

class SherlockModule(JsonEntityModule):
    name = 'sherlock'
    category = 'Username Intelligence'
    input_types = ['username']
    output_types = ['account']
    command_template = 'sherlock {username} --print-found'
    entity_map = {'profile_url': 'Account', 'username': 'Username'}
    def run(self, input_data, context=None):
        return {'input': input_data, 'command': self.build_command(input_data), 'artifacts': [
            {'username': input_data['username'], 'profile_url': f"https://github.com/{input_data['username']}", 'platform': 'GitHub', 'confidence': 0.93},
            {'username': input_data['username'], 'profile_url': f"https://twitter.com/{input_data['username']}", 'platform': 'X', 'confidence': 0.88},
        ]}

class HoleheModule(JsonEntityModule):
    name = 'holehe'
    category = 'Email Intelligence'
    input_types = ['email']
    output_types = ['account']
    command_template = 'holehe {email} --only-used'
    entity_map = {'domain': 'Domain', 'email': 'Email', 'service': 'Account'}
    def run(self, input_data, context=None):
        email = input_data['email']
        domain = email.split('@')[-1]
        return {'input': input_data, 'command': self.build_command(input_data), 'artifacts': [
            {'email': email, 'domain': domain, 'service': 'GitHub', 'confidence': 0.82},
            {'email': email, 'domain': domain, 'service': 'Dropbox', 'confidence': 0.74},
        ]}

class AmassModule(JsonEntityModule):
    name = 'amass'
    category = 'Domain Intelligence'
    input_types = ['domain']
    output_types = ['subdomain']
    command_template = 'amass enum -passive -d {domain} -json {output}'
    entity_map = {'subdomain': 'Domain', 'asn': 'Organization'}
    def run(self, input_data, context=None):
        domain = input_data['domain']
        return {'input': input_data, 'command': self.build_command({**input_data, 'output': '/tmp/amass.json'}), 'artifacts': [
            {'subdomain': f'www.{domain}', 'asn': 'AS64500', 'confidence': 0.91},
            {'subdomain': f'api.{domain}', 'asn': 'AS64500', 'confidence': 0.9},
        ]}

class HttpxModule(JsonEntityModule):
    name = 'httpx'
    category = 'Infrastructure Intelligence'
    input_types = ['domain', 'url']
    output_types = ['http_service']
    command_template = 'httpx -u {target} -json'
    entity_map = {'url': 'Account', 'ip': 'IP'}
    def run(self, input_data, context=None):
        target = input_data.get('target') or input_data.get('domain')
        return {'input': {'target': target}, 'command': self.build_command({'target': target}), 'artifacts': [
            {'url': f'https://{target}', 'ip': '203.0.113.10', 'title': 'Main site', 'confidence': 0.89},
        ]}

class ShodanModule(JsonEntityModule):
    name = 'shodan'
    category = 'Threat Intelligence'
    input_types = ['ip', 'domain']
    output_types = ['service']
    command_template = 'shodan host {ip}'
    entity_map = {'ip': 'IP', 'product': 'Account'}
    def run(self, input_data, context=None):
        ip = input_data.get('ip', '203.0.113.10')
        return {'input': {'ip': ip}, 'command': self.build_command({'ip': ip}), 'artifacts': [
            {'ip': ip, 'product': 'nginx', 'port': 443, 'confidence': 0.8},
            {'ip': ip, 'product': 'OpenSSH', 'port': 22, 'confidence': 0.85},
        ]}

class ExifToolModule(JsonEntityModule):
    name = 'exiftool'
    category = 'Metadata Intelligence'
    input_types = ['file']
    output_types = ['metadata']
    command_template = 'exiftool -json {file}'
    entity_map = {'author_email': 'Email', 'gps': 'Location'}
    def run(self, input_data, context=None):
        return {'input': input_data, 'command': self.build_command(input_data), 'artifacts': [
            {'author_email': 'photographer@example.com', 'gps': '30.2672,-97.7431', 'camera': 'Canon', 'confidence': 0.72},
        ]}

class PhoneInfogaModule(JsonEntityModule):
    name = 'phoneinfoga'
    category = 'Phone Intelligence'
    input_types = ['phone']
    output_types = ['phone_profile']
    command_template = 'phoneinfoga scan -n {phone} -o json'
    entity_map = {'phone': 'Phone', 'carrier': 'Organization'}
    def run(self, input_data, context=None):
        return {'input': input_data, 'command': self.build_command(input_data), 'artifacts': [
            {'phone': input_data['phone'], 'carrier': 'Example Telecom', 'country': 'US', 'confidence': 0.79},
        ]}

class NucleiModule(JsonEntityModule):
    name = 'nuclei'
    category = 'Attack Surface Intelligence'
    input_types = ['url', 'domain']
    output_types = ['finding']
    command_template = 'nuclei -u {target} -jsonl'
    entity_map = {'host': 'Domain', 'template': 'Account'}
    def run(self, input_data, context=None):
        target = input_data.get('target') or input_data.get('url') or input_data.get('domain')
        return {'input': {'target': target}, 'command': self.build_command({'target': target}), 'artifacts': [
            {'host': target, 'template': 'exposed-panel', 'severity': 'medium', 'confidence': 0.76},
        ]}

MODULE_CLASSES: Dict[str, type[JsonEntityModule]] = {cls.name: cls for cls in [SherlockModule, HoleheModule, AmassModule, HttpxModule, ShodanModule, ExifToolModule, PhoneInfogaModule, NucleiModule]}
