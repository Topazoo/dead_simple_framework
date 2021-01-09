# Celery
from celery import Celery, Task
from celery.result import AsyncResult

# Celery Configuration
from celery.schedules import crontab
from kombu.serialization import register

# Task config class
from ..config import TaskConfig

# Task Settings
from ..config import Redis_Settings, RabbitMQ_Settings

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

# Typing
from typing import Union, Dict

# Debug
import logging

# TODO - [Stability]     | Warnings + (Dummy `Task_Manager` if RabbitMQ isn't running [use multiprocess])?
# TODO - [Stability]     | RPC backend if Redis isn't running
# TODO - [Stability]     | Timeouts for all tasks (especially sync tasks)
# TODO - [Useability]    | Retreival method for failed tasks
# TODO - [Useability]    | Use `Celery` via adapter to hide unwanted methods/attributes


class Task_Manager(Celery):
    ''' Client for managing asynchronous tasks 
    
        Allows any tasks specified in the application configuration dictionary's
        `tasks` section to be run or scheduled. Also allows retreival of the most
        recent result of a task. Handles periodic tasks too
    '''

    _app = None                                    # Internal application reference
    _internal_tasks:Dict[str, TaskConfig] = {}     # Internal reference to all dynamically registered tasks
   
    _results_collection = Database_Task._collection     # Collection for task results
    _results_cache_key  = Database_Task._cache_key      # Cache key for latest task result ID storage

    def __init__(self, dynamic_tasks:dict=None, main=None, loader=None, backend=None, amqp=None, events=None, log=None, control=None, set_as_current=True, tasks=None, broker=None, include=None, changes=None, config_source=None, fixups=None, task_cls=None, autofinalize=True, namespace=None, strict_typing=True, result_persistent = False, ignore_result=False, **kwargs):
        # Attach to RabbitMQ to allow tasks to be sent to/processed by any available worker
        broker, backend = RabbitMQ_Settings.RABBITMQ_CONNECTION_STRING, Redis_Settings.REDIS_CONNECTION_STRING
        
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

    def register_tasks(self, tasks:dict):
        ''' Dynamically register all tasks specified in the `tasks` section of the application config with Celery '''

        # Loop over tasks passed in the config
        for task_name, task_config in tasks.items():
            # Create a task config object from a dictionary if a dictionary based config was passed 
            task = self._cast_task(task_name, task_config)

            # Create and register a new Celery task with auto-caching results unless explicitely specified otherwise
            task.set_task(self.task(task.logic, name=task_name, result_serializer='pickle', base=self.get_task_type(task.depends_on), ignore_result=True if task.schedule else False))
            
            # Store a reference in the Task_Manager
            self._internal_tasks[task_name] = task

            # If the task should run on a schedule, set that up
            if task.schedule != None:
                self.register_periodic_task(task)
                

    def register_task_chain(self, task:TaskConfig):
        ''' Register a chain of tasks as a single task. Allows top-level tasks to be called that depend on the results of sub-tasks '''

        # Create a new task that invokes the chain of tasks when executed
        chain_as_task = TaskConfig(name=task.name + '_chain', logic=lambda x=None: self.chain(task.name, task.default_args or [], task.default_kwargs or {}))
        chain_as_task.set_task(self.task(chain_as_task.logic, name=chain_as_task.name, result_serializer='pickle', base=self.get_task_type(task.depends_on), ignore_result=False))
        
        # Store an internal reference to the task chain's top-level task
        self._internal_tasks[chain_as_task.name] = chain_as_task

        return chain_as_task.name


    def register_periodic_task(self, task:TaskConfig):
        ''' Dynamically register a task to run periodically via Celery '''

        # Create a schedule dictoinary in Celery if one does not exist
        if not self.conf.beat_schedule: self.conf.beat_schedule = {}

        # Determine if this scheduled task is a chain and register as such if it is
        task_name = self.register_task_chain(task) if task.depends_on else task.name
        
        # Add the task to the Celery schedule
        self.conf.beat_schedule[task.name] = {
            'task': task_name,
            'schedule': crontab(**task.schedule),
            'args': task.default_args
        }


    @classmethod
    def schedule_task(cls, task_name:str, *args, **kwargs):
        ''' Schedule an asynchronous task to be run by the next available worker.
            The latest result for a task can be retrieved with `get_result()` '''
        
        # Check to see if the relies on sub-tasks and must be chained 
        if cls._internal_tasks[task_name].depends_on:
            return cls._app.chain(task_name, args, kwargs)
        
        # Apply default arguments if none provided
        default_args = cls._internal_tasks[task_name].default_args
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
        task = cls._internal_tasks[task_name]

        # Begin a list of dependent tasks (executed first to last)
        dependants = [task.task.s(*(task.default_args or []), **(task.default_kwargs or {}))] 

        # Add each sub-task to the list of dependant tasks to be executed before the task after it
        while task.depends_on:
            task_name   = task.depends_on
            task        = cls._internal_tasks[task_name]
            dependants.insert(0, task.task.s(*(task.default_args or []), **(task.default_kwargs or {}))) 

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
            task = cls._internal_tasks[task_name]
            to_run.append(task.task.s(*args, **kwargs))

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
    def get_result(cls, task_name:str):
        ''' Get the latest result of a task if it exists
        
        Args:

            task_name (str): The name of the task to retrieve the last result for

        Returns:

           The last stored result for the task
        '''

        # Get the database record ID of the task result from the cache
        result_id = Cache().get_dynamic_dict_value(cls._results_cache_key, task_name)
        if result_id: # Use it to retrieve the result
            with Database(collection=cls._results_collection) as db:
                res =  db.find_one({'_id': ObjectId(result_id)})
                return res['task_result'] if res else res


    @classmethod 
    def get_results(cls, task_name:str):
        ''' Get all stored results for a task 
        
        Args:

            task_name (str): The name of the task to retrieve results for

        Returns:

            All stored results for the task. Only the latest result will be retuned if the task a `Store_Latest_Task` task
        '''

        with Database(collection=cls._results_collection) as db:
            return [res['task_result'] for res in list(db.find({'task_name': task_name}))]


    @staticmethod
    def _cast_task(name:str, task_config:Union[dict, TaskConfig]) -> TaskConfig:
        ''' Takes a task config dictionary and casts it to a `TaskConfig` object 
        
        Args:

            name (str): The name for this task

            task_config (Union[dict, TaskConfig]): The configuration for the task. Can be passed a config dictionary
                or an already created TaskConfig. If the latter if passed, no conversion is necessary
        
        Returns:

            A `Task` object representing the config for that task
        '''
        
        return task_config if isinstance(task_config, TaskConfig) else TaskConfig.from_dict(name, task_config)


    def get_task_type(self, should_store:bool) -> Task:
        ''' Get the type of task to use (different task types store results in different ways)

        Args:

            should_store (bool): Whether or not results should be stored. The type is based on the `store_results` key, if it is present, possible values:
                - None     | Store the last result in the database [default]
                - True     | Store all results in the database
                - False    | Store no results in the database

        Returns:

            The celery task type that should be used to instantiate a given task with based on it's `should_store` attribute
        '''

        if should_store: 
            return Store_Task
        if should_store == False:
            return Task

        return Store_Latest_Task