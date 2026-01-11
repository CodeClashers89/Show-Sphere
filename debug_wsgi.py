import os
import sys
import traceback

# Add project root to path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'showsphere.settings')

try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    print("SUCCESS: WSGI application loaded.")
except Exception:
    print("FAILURE: Could not load WSGI application.")
    traceback.print_exc()
