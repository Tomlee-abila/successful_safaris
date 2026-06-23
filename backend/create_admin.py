import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safari_backend.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_superuser():
    User = get_user_model()
    
    # 1. Try reading from environment variables (e.g. from .env file)
    username = os.environ.get('SUPERUSER_USERNAME')
    email = os.environ.get('SUPERUSER_EMAIL')
    password = os.environ.get('SUPERUSER_PASSWORD')
    
    # 2. If not set, prompt the user (or fall back to defaults)
    if not username:
        username = input("Enter superuser username (default: admin): ").strip() or "admin"
    if not email:
        email = input("Enter superuser email (default: admin@example.com): ").strip() or "admin@example.com"
    if not password:
        import getpass
        password = getpass.getpass("Enter superuser password (default: adminpass123): ").strip() or "adminpass123"
        
    if User.objects.filter(username=username).exists():
        print(f"User '{username}' already exists. Updating password and ensuring superuser privileges...")
        user = User.objects.get(username=username)
        user.set_password(password)
        user.email = email
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print(f"Superuser '{username}' updated successfully!")
    else:
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Superuser '{username}' created successfully!")

if __name__ == '__main__':
    try:
        create_superuser()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)
