# fretes_web/asgi.py (se usar)
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fretes_web.settings.prod")
application = get_asgi_application()
