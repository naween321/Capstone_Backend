try:
    from .env import *
except ModuleNotFoundError:
    from .test import *
