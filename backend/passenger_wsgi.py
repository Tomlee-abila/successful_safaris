import os
import sys

# Point to the directory containing your django project files
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variables for django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safari_backend.settings')

# Import get_wsgi_application from django.core.wsgi to obtain the application callable
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
