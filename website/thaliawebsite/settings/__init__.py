# flake8: noqa
from .settings import *
try:
    from .localsettings import *
except ImportError:
    pass
