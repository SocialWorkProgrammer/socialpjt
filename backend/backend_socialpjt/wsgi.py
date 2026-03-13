"""
WSGI config for backend_socialpjt project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import importlib
import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application


def load_env():
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    try:
        load_dotenv = importlib.import_module("dotenv").load_dotenv
    except ModuleNotFoundError:
        return
    load_dotenv(env_path)


load_env()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_socialpjt.settings')

application = get_wsgi_application()
