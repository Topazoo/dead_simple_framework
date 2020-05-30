''' Dead Simple Framework - Specify APIs with a Python dict and run with one line

    Author: Peter Swanson
'''

from .main import Application
from .database import Database
from .tasks import Task_Manager
from .api.client import API
from .cache import Cache

from .sample import sample_config