import os
import django
from django.conf import settings
from django.test import Client
from django.urls import reverse

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safari_backend.settings')
django.setup()

def run_qa_check():
    client = Client()
    
    # 1. Test Frontend Routes (Basic Connectivity)
    frontend_routes = [
        'home', 'about', 'destinations', 'packages', 'shop', 
        'contact', 'auth', 'booking', 'checkout', 'dashboard', 
        'admin_dashboard', 'sitemap', 'style_guide', 'wireframes'
    ]
    
    print("--- Testing Frontend Routes ---")
    for route in frontend_routes:
        try:
            url = reverse(route)
            response = client.get(url)
            print(f"Route: {route:20} URL: {url:30} Status: {response.status_code}")
            if response.status_code != 200:
                print(f"  [ERROR] Expected 200, got {response.status_code}")
        except Exception as e:
            print(f"  [CRITICAL] Error reversing/getting route {route}: {e}")

    # 2. Test API Endpoints
    api_endpoints = [
        '/api/inventory/pages/',
        '/api/inventory/modules/',
        '/api/inventory/permissions/',
        '/api/schema/',
    ]
    
    print("\n--- Testing API Endpoints ---")
    for endpoint in api_endpoints:
        try:
            response = client.get(endpoint)
            print(f"Endpoint: {endpoint:40} Status: {response.status_code}")
            if response.status_code == 200:
                if 'json' in response.headers.get('Content-Type', ''):
                    data = response.json()
                    if isinstance(data, list):
                        count = len(data)
                    elif isinstance(data, dict):
                        count = len(data.get('results', data))
                    else:
                        count = 'Unknown'
                    print(f"  [DATA] Type: JSON, Count/Len: {count}")
            else:
                 print(f"  [ERROR] Expected 200, got {response.status_code}")
        except Exception as e:
            print(f"  [CRITICAL] Error getting endpoint {endpoint}: {e}")

if __name__ == "__main__":
    run_qa_check()
