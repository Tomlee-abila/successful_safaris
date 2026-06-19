import os
import json

# Setup Django environment FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safari_backend.settings')
import django
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from destinations.models import Destination
from packages.models import SafariPackage
from shop.models import Product

def run_deep_qa():
    client = Client()
    report = []

    # 0. Setup Test Data
    test_email = 'test@example.com'
    test_password = 'password'
    try:
        user = User.objects.get(email=test_email)
    except User.DoesNotExist:
        user = User.objects.create_user(username='test_user_qa', email=test_email, password=test_password)
    
    # Ensure at least one destination, package, product exists for detail tests
    dest = Destination.objects.first()
    pkg = SafariPackage.objects.first()
    prod = Product.objects.first()

    print("--- 1. Route Validation (Public & Protected) ---")
    routes = [
        ('home', reverse('home')),
        ('about', reverse('about')),
        ('destinations', reverse('destinations')),
        ('packages', reverse('packages')),
        ('shop', reverse('shop')),
        ('contact', reverse('contact')),
        ('auth', reverse('auth')),
        ('booking', reverse('booking')),
        ('checkout', reverse('checkout')),
        ('dashboard', reverse('dashboard')),
        ('admin_dashboard', reverse('admin_dashboard')),
        ('sitemap', reverse('sitemap')),
        ('trip_documents', reverse('trip_documents')),
        ('shopping_cart', reverse('shopping_cart')),
    ]
    
    if dest: routes.append(('destination_detail', reverse('destination_detail', args=[dest.id])))
    if pkg: routes.append(('package_detail', reverse('package_detail', args=[pkg.id])))
    if prod: routes.append(('product_detail', reverse('product_detail', args=[prod.id])))

    # We test as a logged-in customer for these
    client.force_login(user)

    for name, url in routes:
        try:
            response = client.get(url)
            # Some pages might redirect (e.g. admin_dashboard if not staff)
            expected_codes = [200]
            if name == 'admin_dashboard':
                 expected_codes = [302, 200]
            
            status = "Working" if response.status_code in expected_codes else "Failed"
            issues = []
            if response.status_code == 200:
                content = response.content.decode('utf-8', errors='ignore')
                if 'logo.png' not in content:
                    issues.append("Missing Logo Reference")
            
            report.append({
                "Category": "Route",
                "Name": name,
                "URL": url,
                "Status": status,
                "Code": response.status_code,
                "Issues": issues
            })
            print(f"[{status}] {name:20} -> {response.status_code} ({len(issues)} issues)")
        except Exception as e:
            print(f"[ERROR] {name:20} -> {e}")

    print("\n--- 2. Workflow Execution (POST simulation) ---")
    workflows = [
        ('Login', reverse('auth'), {'email': test_email, 'password': test_password}),
        ('Booking', reverse('booking'), {'package': pkg.id if pkg else '1', 'guests': 2}),
        ('Contact', reverse('contact'), {'name': 'Tester', 'email': 'tester@example.com', 'message': 'Hello'}),
    ]
    
    client.logout()

    for name, url, data in workflows:
        if name == 'Booking':
             client.force_login(user)
             
        response = client.post(url, data)
        issues = []
        success = response.status_code in [302, 303, 201]
        
        if response.status_code == 200 and name == 'Contact':
             success = False
        
        status = "Working" if success else "Failed"
        if not success:
             issues.append(f"Unexpected status code: {response.status_code}")
        
        report.append({
            "Category": "Workflow",
            "Name": name,
            "URL": url,
            "Status": status,
            "Code": response.status_code,
            "Issues": issues
        })
        print(f"[{status}] {name:20} -> {response.status_code}")

    print("\n--- 3. API Deep Dive ---")
    # API endpoints don't always have names in simple routers or might be nested
    api_tests = [
        ('/inventory/api/pages/', 'GET'),
        ('/inventory/api/modules/', 'GET'),
        ('/inventory/api/permissions/', 'GET'),
        ('/api/schema/', 'GET'),
    ]
    
    for url, method in api_tests:
        response = client.get(url)
        issues = []
        if response.status_code == 200:
            try:
                data = response.json()
                if 'permissions' in url and len(data) < 70:
                    issues.append(f"Incomplete data: expected ~76, got {len(data)}")
            except:
                if 'schema' not in url:
                    issues.append("Invalid JSON response")
        
        report.append({
            "Category": "API",
            "Name": url,
            "URL": url,
            "Status": "Working" if not issues else "Warning",
            "Code": response.status_code,
            "Issues": issues
        })
        print(f"[{'Working' if not issues else 'Warning'}] API {url:30} -> {response.status_code}")

    print("\n--- 4. Static Asset Audit ---")
    static_checks = [
        ('static/images/logo.png', 'Logo')
    ]
    for path, label in static_checks:
        exists = os.path.exists(path)
        print(f"[{'Found' if exists else 'MISSING'}] {label}: {path}")

    with open('qa_evidence.json', 'w') as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    run_deep_qa()
