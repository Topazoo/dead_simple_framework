# Interface class
from .setting import Setting
from .redis_settings import Redis_Settings
# Utilities
import os, kombu, socket, time
from celery import Celery

class RabbitMQ_Settings(Setting):
    ''' Used to specify and validate RabbitMQ settings '''

    CONFIG_TYPE = 'rabbitmq_settings'

    # RabbitMQ Config
    USE_TASKS = os.environ.get('USE_TASKS', 'False').capitalize() == 'True'
    FORCE_START_RABBITMQ = os.environ.get('FORCE_START_RABBITMQ', 'False').capitalize() == 'True'
    FORCE_START_CELERY = os.environ.get('FORCE_START_CELERY', 'False').capitalize() == 'True'
    RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')
    RABBITMQ_PORT = os.environ.get('RABBITMQ_PORT', '5672')
    RABBITMQ_USERNAME = os.environ.get('RABBITMQ_USERNAME', 'guest')
    RABBITMQ_PASSWORD = os.environ.get('RABBITMQ_PASSWORD', 'guest')
    RABBITMQ_CONNECTION_STRING = os.environ.get('RABBITMQ_CONNECTION_STRING')
    RABBITMQ_INSTALLATION_PATH = os.environ.get('RABBITMQ_INSTALLATION_PATH', '/usr/local/opt/rabbitmq/sbin/rabbitmq-server')

    def __init__(self, use_tasks:bool=None, force_start_rabbitmq:bool=None, force_start_celery:bool=None, rabbitmq_host:str=None, 
                    rabbitmq_port:str=None, rabbitmq_username:str=None, rabbitmq_password:str=None, rabbitmq_connection_string:str=None,
                    rabbitmq_installation_path:str=None):

        if use_tasks: RabbitMQ_Settings.USE_TASKS = use_tasks
        if force_start_rabbitmq: RabbitMQ_Settings.FORCE_START_RABBITMQ = force_start_rabbitmq
        if force_start_celery: RabbitMQ_Settings.FORCE_START_CELERY = force_start_celery
        if rabbitmq_host: RabbitMQ_Settings.RABBITMQ_HOST = rabbitmq_host
        if rabbitmq_port: RabbitMQ_Settings.RABBITMQ_PORT = int(rabbitmq_port)
        if rabbitmq_username: RabbitMQ_Settings.RABBITMQ_USERNAME = rabbitmq_username
        if rabbitmq_password: RabbitMQ_Settings.RABBITMQ_PASSWORD = rabbitmq_password
        if rabbitmq_installation_path: RabbitMQ_Settings.RABBITMQ_INSTALLATION_PATH = rabbitmq_installation_path

        if rabbitmq_connection_string: 
            RabbitMQ_Settings.RABBITMQ_CONNECTION_STRING = rabbitmq_connection_string
        else:
            RabbitMQ_Settings.RABBITMQ_CONNECTION_STRING = f"amqp://{RabbitMQ_Settings.RABBITMQ_USERNAME}:{RabbitMQ_Settings.RABBITMQ_PASSWORD}@{RabbitMQ_Settings.RABBITMQ_HOST}:{RabbitMQ_Settings.RABBITMQ_PORT}/"

        # Allow redis to be force started from the application
        if RabbitMQ_Settings.USE_TASKS and RabbitMQ_Settings.FORCE_START_RABBITMQ and not RabbitMQ_Settings.check_rabbitmq_connection():
            print('Force starting RabbitMQ...')
            os.system(RabbitMQ_Settings.RABBITMQ_INSTALLATION_PATH + ' -detached'); time.sleep(4)
            print('Done :)')


    @staticmethod
    def get_log_data():
        ''' Returns a list of the settings to log to console '''

        # If RabbbitMQ is enabled for tasks
        if RabbitMQ_Settings.USE_TASKS:
            rabbitmq_online = RabbitMQ_Settings.check_rabbitmq_connection()
            if RabbitMQ_Settings.USE_TASKS: 
                rabbit_conn_test = 'Connected to RabbitMQ :)' if rabbitmq_online else 'WARNING - RabbitMQ ping failed. Ensure the service is running and config is correct. Defaulting to mutliprocess task engine'
            else: 
                rabbit_conn_test = 'RabbitMQ is disabled via config, defaulting to multiprocess task engine'
        
            return [
                f'RabbitMQ connection string set to [{RabbitMQ_Settings.RABBITMQ_CONNECTION_STRING}]',
                rabbit_conn_test
            ]
        
        return [f'RabbitMQ task engine disabled. Set `USE_TASKS` to True in environment to enable it']


    @staticmethod
    def check_rabbitmq_connection() -> bool:
        ''' Check if RabbitMQ is online '''

        with kombu.Connection(RabbitMQ_Settings.RABBITMQ_CONNECTION_STRING) as c:
            try:
                c.connect()
            except socket.error:
                return False
            else:
                return True
