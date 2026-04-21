"""
asgi.py  — replace your project's existing asgi.py with this file.

Run with Daphne:
    daphne -b 0.0.0.0 -p 8000 your_project.asgi:application

settings.py additions needed:
    INSTALLED_APPS += ["channels", "daphne"]
    ASGI_APPLICATION = "your_project.asgi.application"
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [("127.0.0.1", 6379)]},
        }
    }
    # For development without Redis, use:
    # CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")  # ← update

# Must be called before importing routing so Django apps are ready
django_asgi_app = get_asgi_application()

import your_project.routing as ws_routing  # ← update your_project to your module name

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(ws_routing.websocket_urlpatterns)
    ),
})