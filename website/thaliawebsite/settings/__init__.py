# flake8: noqa
import os
from .settings import *
try:
    from .localsettings import *
except ImportError:
    pass

if os.environ.get('DJANGO_PRODUCTION'):
    from .production import *
if os.environ.get('GITLAB_CI'):
    from .testing import *
