import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safari_backend.settings')
django.setup()

from django.contrib.auth import get_user_model


def _generate_password(length=16):
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_superuser():
    User = get_user_model()
    
    # 1. Try reading from environment variables (e.g. from .env file)
    username = os.environ.get('SUPERUSER_USERNAME')
    email = os.environ.get('SUPERUSER_EMAIL')
    password = os.environ.get('SUPERUSER_PASSWORD')
    
    # 2. If not set, prompt the user (or fall back to defaults)
    if not username:
        try:
            username = input("Enter superuser username (default: admin): ").strip() or "admin"
        except (EOFError, OSError):
            username = "admin"
            print("Non-interactive environment. Using default username: 'admin'")
            
    if not email:
        try:
            email = input("Enter superuser email (default: admin@example.com): ").strip() or "admin@example.com"
        except (EOFError, OSError):
            email = "admin@example.com"
            print("Non-interactive environment. Using default email: 'admin@example.com'")
            
    if not password:
        try:
            import getpass
            entered = getpass.getpass("Enter superuser password (leave blank to generate one): ").strip()
            password = entered or _generate_password()
            if not entered:
                print(f"Generated password: {password}")
        except (EOFError, OSError):
            # Non-interactive run (e.g. a deploy script) with no SUPERUSER_PASSWORD set.
            # Never fall back to a fixed/guessable password here — that's a real
            # credential, not a placeholder, and this script's source is public.
            password = _generate_password()
            print(f"Non-interactive environment. Generated password: {password}")
            print("Copy this down now — it will not be shown again.")

        
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
