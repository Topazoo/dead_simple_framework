# Database
from ..database import Database
from bson import ObjectId

# Cache
from ..cache import Cache

# Celery
from celery import Task

# Errors
from pymongo.errors import InvalidDocument

# Debug
import logging


class Database_Task(Task):
    ''' Base Celery task for storing results in the database '''

    _collection  = '_task_results_'  # Collection to store results in
    _cache_key =   '_task_results_'  # Cache key to store latest result ID (so you don't need to watch Mongo collections)
    _is_setup = False

    # TODO - Distinct task ID field

    def _setup(self):
        ''' Perform database optimizations (once) '''

        # Add index for known lookups
        with Database(collection=self._collection) as db:
            db.create_index([('task_name', 1), ('task_id', -1)])

        self._is_setup = True


    def on_success(self, retval, task_id, args, kwargs):
        ''' Stores the result of an asynchronous task in Mongo when it completes '''

        if not self._is_setup: 
            self._setup()            # Perform initial setup if not done
        
        self.success(retval, task_id, args, kwargs)     # Delegate storage logic to concrete subclasses
    
    def success(self, retval, task_id, args, kwargs):
        ''' Abstract - Implemented by concrete Task classes '''


class Store_Task(Database_Task):
    ''' Celery task that persistently stores the all results in the database '''

    def success(self, retval, task_id, args, kwargs):
        ''' Stores the result of an asynchronous task in Mongo when it completes '''

        # Store the result in MongoDB for retrieval with `Task_Manager.get_result()`
        with Database(collection=self._collection) as db:
            try:
                res = db.insert_one({
                    'task_name': self.name,
                    'task_id': str(task_id),
                    'task_result': retval
                })
            except InvalidDocument as e:
                res = db.insert_one({
                    'task_name': self.name,
                    'task_id': str(task_id),
                    'task_result': str(retval)
                })

        Cache().cache_dynamic_dict(self._cache_key, {self.name: str(res.inserted_id)})


class Store_Latest_Task(Database_Task):
    ''' Celery task that persistently stores the latest result in the database '''

    def success(self, retval, task_id, args, kwargs):
        ''' Stores the result of an asynchronous task in Mongo when it completes '''

        _id = Cache().get_dynamic_dict_value(self._cache_key, self.name) or ObjectId()

        # Store the result in MongoDB for retrieval with `Task_Manager.get_result()`
        with Database(collection=self._collection) as db:
            db.delete_one({'_id': ObjectId(_id)})
            try:
                res = db.insert_one({
                    'task_name': self.name,
                    'task_id': str(task_id),
                    'task_result': retval
                })
            except InvalidDocument as e:
                res = db.insert_one({
                    'task_name': self.name,
                    'task_id': str(task_id),
                    'task_result': str(retval)
                })
        
        Cache().cache_dynamic_dict(self._cache_key, {self.name: str(res.inserted_id)})