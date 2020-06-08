# Database
from ..database import Database

# Celery
from celery import Task

# Utilities
from .utils import insert_persistently_and_cache, upsert_persistently_and_cache

# Errors
from pymongo.errors import InvalidDocument

# Debug
import logging

# TODO - [Logging]       | Combine failure logging with main app stderr if possible?
# TODO - [Stability]     | Automatic retry
# TODO - [Useability]    | Storage of failed tasks for easy retreival [configurable]
# TODO - [Extendability] | Allow results collection and cache key to be overridden
# TODO - [Extendability] | Allow results to be cached directly [new task class]


class Database_Task(Task):
    ''' Base Celery task for storing results in the database '''

    _collection  = '_task_results_'  # Collection to store results in
    _cache_key =   '_task_results_'  # Cache key to store latest result ID (so you don't need to watch Mongo collections)
    _is_setup = False

    # TODO - Distinct task ID field?

    def _setup(self):
        ''' Perform database optimizations (once) '''

        # Add index for known lookups
        with Database(collection=self._collection) as db:
            db.create_index([('task_name', 1), ('task_id', -1)])

        self._is_setup = True


    def on_success(self, retval, task_id, args, kwargs):
        ''' Stores the result of an asynchronous task in Mongo when it completes '''

        if not self._is_setup: 
            self._setup()                               # Perform initial setup if not done
        
        self.success(retval, task_id, args, kwargs)     # Delegate storage logic to concrete subclasses
    
    
    def success(self, retval, task_id, args, kwargs):
        ''' Abstract - Implemented by concrete Task classes '''


class Store_Task(Database_Task):
    ''' Celery task that persistently stores the all results in the database '''

    def success(self, retval, task_id, args, kwargs):
        ''' Stores the result of an asynchronous task in Mongo when it completes '''

        data = {'task_name': self.name, 'task_id': str(task_id), 'task_result': retval}
        try:
            # Store the result in MongoDB for retrieval with `Task_Manager.get_result()`
            insert_persistently_and_cache(self._collection, self._cache_key, data, self.name)
        except InvalidDocument as e:
            # Coerce task result to string if it can't be serialized 
            data = {'task_name': self.name, 'task_id': str(task_id), 'task_result': str(retval)}
            insert_persistently_and_cache(self._collection, self._cache_key, data, self.name)
        

class Store_Latest_Task(Database_Task):
    ''' Celery task that persistently stores the latest result in the database '''

    def success(self, retval, task_id, args, kwargs):
        ''' Stores the result of an asynchronous task in Mongo when it completes '''

        data = {'task_name': self.name, 'task_id': str(task_id), 'task_result': retval}
        try:
            # Store the result in MongoDB for retrieval with `Task_Manager.get_result()`
            upsert_persistently_and_cache(self._collection, self._cache_key, data, self.name)
        except InvalidDocument as e:
            # Coerce task result to string if it can't be serialized 
            data = {'task_name': self.name, 'task_id': str(task_id), 'task_result': str(retval)}
            upsert_persistently_and_cache(self._collection, self._cache_key, data, self.name)
        