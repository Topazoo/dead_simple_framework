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
from celery import chain
import os, json

# Debug
import logging


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

    def _get_host(self):
        ''' Connection string for RabbitMQ '''

        # TODO - Allow config from dictionary

        # Check the environment for a custom config, then default to localhost
        host = os.environ.get('RABBITMQ_HOST', 'localhost')
        port = os.environ.get('RABBITMQ_PORT', '5672')
        username = os.environ.get('RABBITMQ_USERNAME', 'guest')
        password = os.environ.get('RABBITMQ_PASSWORD', 'guest')

        return f"amqp://{username}:{password}@{host}:{port}/"


    def __init__(self, dynamic_tasks:dict=None, main=None, loader=None, backend='rpc://', amqp=None, events=None, log=None, control=None, set_as_current=True, tasks=None, broker=None, include=None, changes=None, config_source=None, fixups=None, task_cls=None, autofinalize=True, namespace=None, strict_typing=True, result_persistent = False, ignore_result=True, **kwargs):
        # Attach to RabbitMQ to allow tasks to be sent to/processed by any available worker
        broker = self._get_host()
        
        # Override path to tasks to simplify invoking Celery from the command line
        super().__init__(main='dead_simple_framework', loader=loader, backend=backend, amqp=amqp, events=events, log=log, control=control, set_as_current=set_as_current, tasks=tasks, broker=broker, include=include, changes=changes, config_source=config_source, fixups=fixups, task_cls=task_cls, autofinalize=autofinalize, namespace=namespace, strict_typing=strict_typing, **kwargs)
        
        # Set Pickle as the task result serializer
        self.register_serializer()

        # Register all tasks specified in the `tasks` section of the application config
        if dynamic_tasks:
            self.register_tasks(dynamic_tasks)

        Task_Manager._app = self

    
    def register_serializer(self):
        ''' Register Pickle as the serializer for task results '''

        # Update the Celery configuration
        self.conf.update(
            task_serializer='pickle',
            result_serializer='pickle',
            accept_content=['pickle']
        )

    def _get_task_type(self, task_params:dict):
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
            new_task = self.task(task_params['logic'], name=task_name, result_serializer='pickle', base=task_type)
            
            # Store a reference in the Task_Manager
            self._internal_tasks[task_name] = {'task': new_task, 'params': task_params}

            # If the task should run on a schedule, set that up
            if task_params.get('schedule') != None:
                self.register_periodic_task(task_name, new_task, task_params)
                

    def register_task_chain(self, task_name:str, task_params:dict):
        ''' Register a chain of tasks as a single task. Allows top-level tasks to be called that depend on the results of sub-tasks '''
       
        _task_name = task_name

        # Create a new function that creates the task chain when called
        t = lambda x=None: self.create_chain(_task_name, task_params.get('args', []), task_params.get('kwargs', {}))
        
        # Add a unique suffix for the function and chained task
        task_name += '_chain'
        t.__name__ = task_name

        # Get the type of task to create based on the task parameters
        task_type = self._get_task_type(task_params)

        # Create a new task that invokes the chain of tasks when executed
        new_task = self.task(t, name=task_name, result_serializer='pickle', ignore_result=True, base=task_type)
        
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
            return cls._app.create_chain(task_name, args, kwargs)
        
        # Apply default arguments if none provided
        default_args = cls._internal_tasks[task_name]['params'].get('args')
        if not args and default_args:
            args = default_args

        return cls._app.send_task(task_name, args, kwargs)


    @classmethod
    def run_task(cls, task_name:str, *args, **kwargs):
        # TODO - Timeouts
        ''' Run an asynchronous task and get the result immediately (force synchronous)'''

        cache = Cache()

        is_started = False
        last_id = Cache().get_dynamic_dict_value(cls._results_cache_key, task_name)
        # Wait for ID of cached result to update then return
        while cache.get_dynamic_dict_value(cls._results_cache_key, task_name) == last_id:
            if not is_started:
                # Send the task to the next available worker once
                cls.schedule_task(task_name, *args, **kwargs)
                is_started = True

        # Fetch the result from the cache and return
        return cls.get_result(task_name)


    @classmethod
    def create_chain(cls, task_name:str, *args, **kwargs) ->list:
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
    def get_result(cls, task_name):
        ''' Get the latest result of a task if it exists '''

        result_id = Cache().get_dynamic_dict_value(cls._results_cache_key, task_name)
        if result_id:
            with Database(collection=cls._results_collection) as db:
                res =  db.find_one({'_id': ObjectId(result_id)})
                return res['task_result'] if res else res


    @classmethod 
    def get_results(cls, task_name):
        ''' Get all stored results for a task '''

        with Database(collection=cls._results_collection) as db:
            return list(db.find({'task_name': task_name}))
