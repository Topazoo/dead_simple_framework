from celery import Celery
import os, logging

class Task_Manager(Celery):
    ''' Wrapper for celery base class to allow dynamic task registration '''

    _app = None # Internal self-reference

    def _get_host(self):
        ''' Hook in RabbitMQ '''

        host = os.environ.get('RABBITMQ_HOST', 'localhost')
        port = os.environ.get('RABBITMQ_PORT', '5672')
        username = os.environ.get('RABBITMQ_USERNAME', 'guest')
        password = os.environ.get('RABBITMQ_PASSWORD', 'guest')

        return f"amqp://{username}:{password}@{host}:{port}/"


    def __init__(self, dynamic_tasks:dict=None, main=None, loader=None, backend='rpc://', amqp=None, events=None, log=None, control=None, set_as_current=True, tasks=None, broker=None, include=None, changes=None, config_source=None, fixups=None, task_cls=None, autofinalize=True, namespace=None, strict_typing=True, result_persistent = True, ignore_result=False, **kwargs):
        broker = self._get_host()
        
        super().__init__(main='dead_simple_framework', loader=loader, backend=backend, amqp=amqp, events=events, log=log, control=control, set_as_current=set_as_current, tasks=tasks, broker=broker, include=include, changes=changes, config_source=config_source, fixups=fixups, task_cls=task_cls, autofinalize=autofinalize, namespace=namespace, strict_typing=strict_typing, **kwargs)

        if dynamic_tasks:
            self.register_tasks(dynamic_tasks)


    def register_tasks(self, tasks:dict):
        ''' Dynamically registered passed tasks with Celery '''

        for task_name, task_params in tasks.items():
            if task_params['logic'].__name__ == '<lambda>':
                task_params['logic'].__name__ = task_name

            self.task(task_params['logic'], name=task_name)


    @classmethod
    def run_task(cls, task_name:str, *args, **kwargs):
        ''' Wrapper to simplify firing tasks from route logic '''

        return cls._app.send_task('add', *args, **kwargs)