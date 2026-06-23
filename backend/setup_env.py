import os
import secrets
import string

def generate_secret_key():
    # Generates a secure 50-character random key for Django signing
    chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(chars) for _ in range(50))

def main():
    example_path = '.env.example'
    env_path = '.env'
    
    if os.path.exists(env_path):
        print(f"Error: '{env_path}' already exists. We will not overwrite it to protect your settings.")
        return
        
    if not os.path.exists(example_path):
        print(f"Error: Template '{example_path}' not found.")
        return
        
    print(f"Copying '{example_path}' to '{env_path}'...")
    with open(example_path, 'r') as example_file:
        content = example_file.read()
        
    # Replace the default secret key placeholder with a fresh generated one
    new_secret_key = generate_secret_key()
    content = content.replace('django-insecure-your-secret-key-here', new_secret_key)
    
    with open(env_path, 'w') as env_file:
        env_file.write(content)
        
    print(f"Successfully created '{env_path}' with a secure, random DJANGO_SECRET_KEY!")

if __name__ == '__main__':
    main()
