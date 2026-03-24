import os
import requests

class UsernameDiscovery:
    def __init__(self, username):
        self.username = username
        self.api_url = 'https://api.example.com/usernames'

    def check_username_availability(self):
        response = requests.get(f'{self.api_url}/{self.username}')
        if response.status_code == 200:
            return response.json().get('available', False)
        return False

    def fetch_related_usernames(self):
        response = requests.get(f'{self.api_url}/related/{self.username}')
        if response.status_code == 200:
            return response.json().get('related_usernames', [])
        return []

# Example usage
if __name__ == '__main__':
    discovery = UsernameDiscovery('testuser')
    is_available = discovery.check_username_availability()
    related = discovery.fetch_related_usernames()
    print(f'Username available: {is_available}')
    print(f'Related usernames: {related}')