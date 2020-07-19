
# Interface class
from .config import Config

# Typing
from typing import Callable


class TaskConfig(Config):
    ''' Used to specify a task in the config dictionary '''

    CONFIG_TYPE = 'task'

    def __init__(self, name:str, logic:Callable, schedule:dict=None, default_args:tuple=None, default_kwargs:dict=None, depends_on:str=None, store_results:bool=None):
        ''' Initialize a new task to add to the task config 
        
        Args:
            
            name (str): The name for this task

            logic (Callable): The function to run when this task is executed

            schedule (dict): If passed allows the task to run on a schedule (see the `Schedule` config class for more info)
            
            default_args (tuple): A tuple of default arguments to pass to the task
            
            default_kwargs (dict): A dictionary of default keyword arguments + values to pass to the task

            depends_on (str): The name of another task that this one depends on. Used to create chains of dependant tasks

            store_results (bool): If set to True, all results for this task will be store. If set to false no results will be stored.
                If not set, only the latest result will be saved (default behavior)
        '''

        self.name = name
        self.logic = logic
        self.schedule = schedule # TODO - Add schedule config
        self.default_args = default_args
        self.default_kwargs = default_kwargs
        self.depends_on = depends_on
        self.store_results = store_results

        # Set externally
        self.task = None

        # Set the name of the function for the task to the task's name
        self.logic.__name__ = name

    def set_task(self, task):
        ''' Set the actual Celery task for this class '''

        assert not self.task, f"Task.set_task() error for task [{self.name}] | A Celery task is already set!"

        self.task = task
