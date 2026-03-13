"""
ASGI config for socialpjt project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import importlib
import os
from pathlib import Path

from django.core.asgi import get_asgi_application


def load_env():
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    try:
        load_dotenv = importlib.import_module("dotenv").load_dotenv
    except ModuleNotFoundError:
        return
    load_dotenv(env_path)


load_env()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_socialpjt.settings')

application = get_asgi_application()
