import nmap
import json
import xml.etree.ElementTree as ET

class NmapScanner:
    def __init__(self, target):
        self.target = target
        self.nm = nmap.PortScanner()

    def scan(self, arguments=''): 
        try:
            print(f'Starting scan on {self.target}...')
            self.nm.scan(self.target, arguments)
            print('Scan completed.')
        except Exception as e:
            print(f'Error during scan: {str(e)}')

    def parse_output(self, output_format='json'):
        if output_format == 'json':
            return json.dumps(self.nm.csv())
        elif output_format == 'xml':
            return nmap.xml_to_json(self.nm)
        else:
            raise ValueError('Unsupported output format. Use json or xml.')

    def show_results(self):
        print(self.nm.all_hosts())
        for host in self.nm.all_hosts():
            print(f'Host : {host} ({self.nm[host].hostname()})')
            print(f'State : {self.nm[host].state()}')
            for proto in self.nm[host].all_protocols():
                lport = self.nm[host][proto].keys()
                for port in sorted(lport):
                    print(f'Port : {port}\tState : {self.nm[host][proto][port]}')

    def detect_os(self):
        os_info = self.nm[self.target]['osmatch']
        return os_info

    def run_nse_scripts(self, script):
        self.nm[host].run_nse(script)

if __name__ == '__main__':
    target = '192.168.1.1'  # Example target
    scanner = NmapScanner(target)
    scanner.scan(arguments='-sS -sV -O')  # Example arguments for scanning
    scanner.show_results()  
    os_info = scanner.detect_os()
    print(f'OS Info: {os_info}')