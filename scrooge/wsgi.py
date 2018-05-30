"""
WSGI config for scrooge project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""
import os
import confy
from pathlib import Path

# These lines are required for interoperability between local and container environments.
d = Path(__file__).resolve().parents[1]
dot_env = os.path.join(str(d), '.env')
if os.path.exists(dot_env):
    confy.read_environment_file(dot_env)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scrooge.settings")

application = get_wsgi_application()
