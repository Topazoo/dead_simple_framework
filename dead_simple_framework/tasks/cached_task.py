# Cache
from ..cache.main import Cache

# Celery
from celery import Task

# Debug
import logging


class Cached_Task(Task):
    ''' Celery task that persistently stores the latest result in the Cache '''

    _cache = Cache()                # Cache for task result IDs
    _cache_path = '_task_results_'  # Key to store them at in the cache


    def on_success(self, retval, task_id, args, kwargs):
        ''' Cache task result if completed '''

        self._cache.cache_dynamic_dict(self._cache_path, {self.name: retval})
