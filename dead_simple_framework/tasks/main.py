# Celery
from celery import Celery, Task
from celery.result import AsyncResult

# Celery Configuration
from celery.schedules import crontab
from kombu.serialization import register

# Custom Tasks
from .task import Database_Task, Store_Task, Store_Latest_Task

# Database
from ..database import Database
from bson import ObjectId

# Cache
from ..cache import Cache

# Utilities
from .utils import upsert_persistently_and_cache
from celery import chain, group
import os, json

# Debug
import logging

# TODO - [Stability]     | Warnings + (Dummy `Task_Manager` if RabbitMQ isn't running [use multiprocess])?
# TODO - [Stability]     | RPC backend if Redis isn't running
# TODO - [Stability]     | Timeouts for all tasks (especially sync tasks)
# TODO - [Useability]    | Retreival method for failed tasks
# TODO - [Useability]    | Use `Celery` via adapter to hide unwanted methods/attributes
# TODO - [Useability]     | TaskConfig class to allow a task to be created with hinting/linting enabled
# TODO - [Extendability] | Allow ampq/results backend/celery config to be set in app config, use env as a redundancy


class Task_Manager(Celery):
    ''' Client for managing asynchronous tasks 
    
        Allows any tasks specified in the application configuration dictionary's
        `tasks` section to be run or scheduled. Also allows retreival of the most
        recent result of a task. Handles periodic tasks too
    '''

    _app = None              # Internal application reference
    _internal_tasks = {}     # Internal reference to all dynamically registered tasks [TODO - Class rather than dictionary]
   
    _results_collection = Database_Task._collection     # Collection for task results
    _results_cache_key  = Database_Task._cache_key      # Cache key for latest task result ID storage

    def _get_ampq_host(self):
        ''' Connection string for RabbitMQ broker '''

        # Check the environment for a custom config, then default to localhost
        host = os.environ.get('RABBITMQ_HOST', 'localhost')
        port = os.environ.get('RABBITMQ_PORT', '5672')
        username = os.environ.get('RABBITMQ_USERNAME', 'guest')
        password = os.environ.get('RABBITMQ_PASSWORD', 'guest')

        return f"amqp://{username}:{password}@{host}:{port}/"

    def _get_redis_host(self):
        ''' Connection string for Redis results backend '''

        host=os.environ.get('REDIS_HOST', 'localhost')
        port=os.environ.get('REDIS_PORT', '6379')
        db = os.environ.get('REDIS_DB', '0')

        return f'redis://{host}:{port}/{db}'


    def __init__(self, dynamic_tasks:dict=None, main=None, loader=None, backend=None, amqp=None, events=None, log=None, control=None, set_as_current=True, tasks=None, broker=None, include=None, changes=None, config_source=None, fixups=None, task_cls=None, autofinalize=True, namespace=None, strict_typing=True, result_persistent = False, ignore_result=False, **kwargs):
        # Attach to RabbitMQ to allow tasks to be sent to/processed by any available worker
        broker, backend = self._get_ampq_host(), self._get_redis_host()
        
        # Override path to tasks to simplify invoking Celery from the command line
        super().__init__(main='dead_simple_framework', loader=loader, backend=backend, amqp=amqp, events=events, log=log, control=control, set_as_current=set_as_current, tasks=tasks, broker=broker, include=include, changes=changes, config_source=config_source, fixups=fixups, task_cls=task_cls, autofinalize=autofinalize, namespace=namespace, strict_typing=strict_typing, **kwargs)
        
        # Set Pickle as the task result serializer
        self.configure()

        # Register all tasks specified in the `tasks` section of the application config
        if dynamic_tasks:
            self.register_tasks(dynamic_tasks)

        Task_Manager._app = self

    def configure(self):
        ''' Optimize Celery configuration '''

        # Optimize the Celery configuration and set results serializer
        self.conf.update(
            task_create_missing_queues = True,
            task_acks_late = True,
            worker_prefetch_multiplier = 1,
            result_expires = 1,
            task_serializer='pickle',
            result_serializer='pickle',
            accept_content=['pickle']
        )

    @staticmethod
    def _get_task_type(task_params:dict):
        ''' Get the type of task to use (different task types store results in different ways)

            The type is based on the `store_results` key, if it is present, possible values:
              - 'all'    | Store all results in the database
              - 'latest' | Store the last result in the database [default]
        '''

        _type = task_params.get('store_results')
        if _type == 'all': 
            return Store_Task
        if _type == False:
            return Task

        return Store_Latest_Task

    def register_tasks(self, tasks:dict):
        ''' Dynamically register all tasks specified in the `tasks` section of the application config with Celery '''

        # Loop over tasks passed in the config
        for task_name, task_params in tasks.items():
            # Set the name of the function for the task to the task's name
            task_params['logic'].__name__ = task_name

            # Get the type of task to create based on the task parameters
            task_type = self._get_task_type(task_params)

            # Create and register a new Celery task with auto-caching results unless explicitely specified otherwise
            new_task = self.task(task_params['logic'], name=task_name, result_serializer='pickle', base=task_type, ignore_result=True if task_params.get('schedule') else False)
            
            # Store a reference in the Task_Manager
            self._internal_tasks[task_name] = {'task': new_task, 'params': task_params}

            # If the task should run on a schedule, set that up
            if task_params.get('schedule') != None:
                self.register_periodic_task(task_name, new_task, task_params)
                

    def register_task_chain(self, task_name:str, task_params:dict):
        ''' Register a chain of tasks as a single task. Allows top-level tasks to be called that depend on the results of sub-tasks '''
       
        _task_name = task_name

        # Create a new function that creates the task chain when called
        t = lambda x=None: self.chain(_task_name, task_params.get('args', []), task_params.get('kwargs', {}))
        
        # Add a unique suffix for the function and chained task
        task_name += '_chain'
        t.__name__ = task_name

        # Get the type of task to create based on the task parameters
        task_type = self._get_task_type(task_params)

        # Create a new task that invokes the chain of tasks when executed
        new_task = self.task(t, name=task_name, result_serializer='pickle', base=task_type, ignore_result=False)
        
        # Store an internal reference to the task chain's top-level task
        self._internal_tasks[task_name] = {'task': new_task, 'params': task_params}

        return task_name


    def register_periodic_task(self, task_name:str, task:Celery.Task, task_params:dict):
        ''' Dynamically register a task to run periodically via Celery '''

        # Get the schedule specified for the task
        schedule = task_params['schedule']

        # Create a schedule dictoinary in Celery if one does not exist
        if not self.conf.beat_schedule: self.conf.beat_schedule = {}

        # Determine if this scheduled task is a chain and register as such if it is
        if task_params.get('depends_on'):
            task_name = self.register_task_chain(task_name, task_params)
        
        # Add the task to the Celery schedule
        self.conf.beat_schedule[task_name] = {
            'task': task_name,
            'schedule': crontab(**schedule),
            'args': task_params.get('args')
        }


    @classmethod
    def schedule_task(cls, task_name:str, *args, **kwargs):
        ''' Schedule an asynchronous task to be run by the next available worker.
            The latest result for a task can be retrieved with `get_result()` '''
        
        # Check to see if the relies on sub-tasks and must be chained 
        if cls._internal_tasks[task_name]['params'].get('depends_on'):
            return cls._app.chain(task_name, args, kwargs)
        
        # Apply default arguments if none provided
        default_args = cls._internal_tasks[task_name]['params'].get('args')
        if not args and default_args:
            args = (default_args,)

        # Drop the result in Celery/Redis as we're relying on the framework to cache them
        return cls._app.send_task(task_name, *args, **kwargs, ignore_result=True)


    @classmethod
    def run_task(cls, task_name:str, sync=True, *args, **kwargs):
        ''' Run an asynchronous task. Gets the result immediately if sync=True (force synchronous)'''

        if not sync: return cls.schedule_task(task_name, *args, **kwargs)

        cache = Cache()

        is_started = False
        last_id = cache.get_dynamic_dict_value(cls._results_cache_key, task_name)
        # Wait for ID of cached result to update then return
        while cache.get_dynamic_dict_value(cls._results_cache_key, task_name) == last_id:
            if not is_started:
                # Send the task to the next available worker once
                cls.schedule_task(task_name, *args, **kwargs)
                is_started = True

        # Fetch the result from the cache and return
        return cls.get_result(task_name)


    @classmethod
    def chain(cls, task_name:str, *args, **kwargs) ->list:
        ''' Form a chain of dependant sub-tasks for a given task '''

        # Get the top level task and its parameters
        first_task                      = cls._internal_tasks[task_name]['task']
        task_params = first_task_params = cls._internal_tasks[task_name]['params']

        # Begin a list of dependent tasks (executed first to last)
        dependants = [first_task.s(*task_params.get('args', []), **task_params.get('kwargs', {}))] 

        # Add each sub-task to the list of dependant tasks to be executed before the task after it
        while task_params.get('depends_on'):
            task_name   = task_params.get('depends_on')
            task        = cls._internal_tasks[task_name]['task']
            task_params = cls._internal_tasks[task_name]['params']
            
            dependants.insert(0, task.s(*task_params.get('args', []), **task_params.get('kwargs', {}))) 

        # Create a chain of tasks allowing the argument of the first to be passed to the next and so on
        return chain(*dependants)()


    @classmethod
    def parallelize(cls, tasks, cache_as:str=None):
        ''' Takes a list of tasks (in the same format as `schedule_task()`) and runs them in parallel 
            If `cache_as` is set, the result will be cached as if it were a task and will be accessible via `
        '''

        to_run = []
        for task in tasks: # Create signature (with args) for every task being run in parallel
            task_name, args, kwargs = task[0], task[1] if len(task) > 1 else [], task[2] if len(task) > 2 else {}
            task_obj, task_params = cls._internal_tasks[task_name]['task'], cls._internal_tasks[task_name]['params']
            to_run.append(task_obj.s(*args, **kwargs))

        # Run the task and immediately get the result
        task = group(to_run).apply_async()

        # Allow sync subtasks in the event `parallelize` is used within another task
        result = task.get(disable_sync_subtasks=False)

        # Cache the data like a regular task if specified
        if cache_as:
            data = {'task_name': cache_as, 'task_id': str(task.id), 'task_result': result}
            upsert_persistently_and_cache(cls._results_collection, cls._results_cache_key, data, cache_as)
        
        return result


    @classmethod 
    def get_result(cls, task_name):
        ''' Get the latest result of a task if it exists '''

        # Get the database record ID of the task result from the cache
        result_id = Cache().get_dynamic_dict_value(cls._results_cache_key, task_name)
        if result_id: # Use it to retrieve the result
            with Database(collection=cls._results_collection) as db:
                res =  db.find_one({'_id': ObjectId(result_id)})
                return res['task_result'] if res else res


    @classmethod 
    def get_results(cls, task_name):
        ''' Get all stored results for a task '''

        with Database(collection=cls._results_collection) as db:
            return [res['task_result'] for res in list(db.find({'task_name': task_name}))]
