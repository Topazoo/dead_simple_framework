# Interface class
from .setting import Setting

# Utilities
import os, redis

class Redis_Settings(Setting):
    ''' Used to specify and validate Redis settings '''

    CONFIG_TYPE = 'redis_settings'

    # Redis Config
    USE_REDIS = os.environ.get('USE_REDIS', 'False').capitalize() == 'True'
    FORCE_START_REDIS = os.environ.get('FORCE_START_REDIS', 'False').capitalize() == 'True'
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
    REDIS_DB = os.environ.get('REDIS_DB', 0)
    REDIS_INSTALLATION_PATH = os.environ.get('REDIS_INSTALLATION_PATH', '/usr/local/bin/redis-server')
    REDIS_CONNECTION_STRING = os.environ.get('REDIS_CONNECTION_STRING')

    def __init__(self, use_redis:bool=None, force_start_redis:bool=None, redis_host:str=None, redis_port:str=None, redis_db:str=None, redis_connection_string:str=None):

        if use_redis: Redis_Settings.USE_REDIS = use_redis
        if force_start_redis: Redis_Settings.FORCE_START_REDIS = force_start_redis
        if redis_host: Redis_Settings.REDIS_HOST = redis_host
        if redis_port: Redis_Settings.REDIS_PORT = int(redis_port)
        if redis_db: Redis_Settings.REDIS_DB = int(redis_db)
        if redis_connection_string:
            Redis_Settings.REDIS_CONNECTION_STRING = redis_connection_string
        else:
            Redis_Settings.REDIS_CONNECTION_STRING = f'redis://{Redis_Settings.REDIS_HOST}:{Redis_Settings.REDIS_PORT}/{Redis_Settings.REDIS_DB}'

        # Allow redis to be force started from the application
        if Redis_Settings.FORCE_START_REDIS and not Redis_Settings.check_redis_connection():
            os.system(f'{Redis_Settings.REDIS_INSTALLATION_PATH} --daemonize yes')

    @staticmethod
    def get_log_data():
        ''' Returns a list of the settings to log to console '''

        # If Redis is enabled
        if Redis_Settings.USE_REDIS:
            redis_online = Redis_Settings.check_redis_connection()
            if Redis_Settings.USE_REDIS: 
                conn_test = 'Connected to Redis :)' if redis_online else 'WARNING - Redis ping failed. Ensure the service is running and config is correct. Defaulting to in-memory cache'
            else: 
                conn_test = 'Redis is disabled via config, defaulting to in-memory cache'
            
            return [
                f'Redis host set to [{Redis_Settings.REDIS_HOST}]',
                f'Redis port set to [{Redis_Settings.REDIS_PORT}]',
                f'Redis default db set to [{Redis_Settings.REDIS_DB}]',
                conn_test
            ]
        
        return [f'Redis caching disabled. Set `USE_REDIS` to True in environment to enable it']

    @staticmethod
    def check_redis_connection() -> bool:
        ''' Check if Redis is online '''

        try: # Determine if redis is online
            return redis.Redis(host=Redis_Settings.REDIS_HOST, port=Redis_Settings.REDIS_PORT, db=Redis_Settings.REDIS_DB, socket_connect_timeout=1).ping()
        except:
            return False
