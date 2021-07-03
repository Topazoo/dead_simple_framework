# Interface class
from .setting import Setting

# Utilities
import os, pymongo

class MongoDB_Settings(Setting):
    ''' Used to specify and validate MongoDB settings '''

    CONFIG_TYPE = 'mongodb_settings'

    # MongoDB Config
    MONGODB_ATLAS = os.environ.get('MONGODB_ATLAS', 'False').capitalize() == 'True'
    MONGODB_HOST = os.environ.get('MONGODB_HOST', 'localhost')
    MONGODB_PORT = os.environ.get('MONGODB_PORT', 27017)
    MONGODB_USERNAME = os.environ.get('MONGODB_USERNAME', '')
    MONGODB_PASSWORD = os.environ.get('MONGODB_PASSWORD', '')
    MONGODB_DEFAULT_DB = os.environ.get('MONGODB_DEFAULT_DB', 'db')
    MONGODB_DEFAULT_COLLECTION = os.environ.get('MONGODB_DEFAULT_COLLECTION', 'data')
    MONGODB_CONNECTION_STRING = os.environ.get('MONGODB_CONNECTION_STRING')
    MONGODB_CONN_TIMEOUT = int(os.environ.get('MONGODB_CONN_TIMEOUT', 600))
    MONGODB_DATA_PATH = os.environ.get('MONGODB_DATA_PATH', os.path.expanduser('~/data/db'))
    MONGODB_LOG_PATH = os.environ.get('MONGODB_LOG_PATH', os.path.expanduser('/tmp/mongo.log'))
    MONGODB_INSTALLATION_PATH = os.environ.get('RABBITMQ_INSTALLATION_PATH', '/usr/local/bin/mongod')
    FORCE_START_MONGODB = os.environ.get('FORCE_START_MONGODB', 'True').capitalize() == 'True'

    def __init__(self, mongodb_atlas:bool=None, mongodb_host:str=None, mongodb_port:str=None, mongodb_username:str=None,
                    mongodb_password:str=None, mongodb_default_db:str=None, mongodb_default_collection:str=None,
                    mongodb_connection_string:str=None, mongodb_data_path:str=None, mongodb_log_path:str=None, 
                    force_start_mongodb:bool=None, mongodb_installation_path:str=None, mongodb_conn_timeout:int=None):

        if mongodb_atlas: MongoDB_Settings.MONGODB_ATLAS = mongodb_atlas
        if mongodb_host: MongoDB_Settings.MONGODB_HOST = mongodb_host
        if mongodb_port: MongoDB_Settings.MONGODB_PORT = mongodb_port
        if mongodb_username: MongoDB_Settings.MONGODB_USERNAME = mongodb_username
        if mongodb_password: MongoDB_Settings.MONGODB_PASSWORD = mongodb_password
        if mongodb_default_db: MongoDB_Settings.MONGODB_DEFAULT_DB = mongodb_default_db
        if mongodb_default_collection: MongoDB_Settings.MONGODB_DEFAULT_COLLECTION = mongodb_default_collection
        if mongodb_data_path: MongoDB_Settings.MONGODB_DATA_PATH = mongodb_data_path
        if mongodb_log_path: MongoDB_Settings.MONGODB_LOG_PATH = mongodb_log_path
        if mongodb_installation_path: MongoDB_Settings.MONGODB_INSTALLATION_PATH = mongodb_installation_path
        if force_start_mongodb: MongoDB_Settings.FORCE_START_MONGODB = force_start_mongodb
        if mongodb_conn_timeout: MongoDB_Settings.MONGODB_CONN_TIMEOUT =mongodb_conn_timeout
        if mongodb_connection_string: 
            MongoDB_Settings.MONGODB_CONNECTION_STRING = mongodb_connection_string
        else:
            auth = f"{MongoDB_Settings.MONGODB_USERNAME}:{MongoDB_Settings.MONGODB_PASSWORD}@"
            if not MongoDB_Settings.MONGODB_ATLAS:
                MongoDB_Settings.MONGODB_CONNECTION_STRING = f'mongodb://' + (auth + MongoDB_Settings.MONGODB_HOST if auth.strip() != ':@' else MongoDB_Settings.MONGODB_HOST)
            else:
                MongoDB_Settings.MONGODB_CONNECTION_STRING = f'mongodb+srv://' + (auth + MongoDB_Settings.MONGODB_HOST if auth.strip() != ':@' else MongoDB_Settings.MONGODB_HOST) + f'/{MongoDB_Settings.MONGODB_DEFAULT_DB}?retryWrites=true&w=majority'
        # Allow MongoDB to be force started
        MongoDB_Settings.check_mongodb_connection(MongoDB_Settings.FORCE_START_MONGODB)
            
    @staticmethod
    def get_log_data():
        ''' Returns a list of the settings to log to console '''

        MongoDB_Settings.check_mongodb_connection()
        if not MongoDB_Settings.MONGODB_ATLAS:
            conn_str = f'MongoDB connection string set to [{MongoDB_Settings.MONGODB_CONNECTION_STRING}:{MongoDB_Settings.MONGODB_PORT}]'
            log_data = [
                f'MongoDB data path set to [{MongoDB_Settings.MONGODB_DATA_PATH}]',
                f'MongoDB log path set to [{MongoDB_Settings.MONGODB_LOG_PATH}]',
            ]
        else:
            conn_str = f'MongoDB connection string set to Atlas URL [{MongoDB_Settings.MONGODB_CONNECTION_STRING}'
            log_data = []

        return [
            conn_str,
            f'MongoDB default database set to [{MongoDB_Settings.MONGODB_DEFAULT_DB}]',
            f'MongoDB default collection set to [{MongoDB_Settings.MONGODB_DEFAULT_COLLECTION}]',
            *log_data,
            'Connected to MongoDB :)'
        ]

    @staticmethod
    def check_mongodb_connection(can_force_start:bool=False) -> bool:
        ''' Check if MongoDB is online '''

        try: # Determine if MongoDB is online
            if not MongoDB_Settings.MONGODB_ATLAS:
                return True if pymongo.MongoClient(host=MongoDB_Settings.MONGODB_CONNECTION_STRING, port=MongoDB_Settings.MONGODB_PORT, serverSelectionTimeoutMS=MongoDB_Settings.MONGODB_CONN_TIMEOUT).server_info() else False
            else:
                return True if pymongo.MongoClient(MongoDB_Settings.MONGODB_CONNECTION_STRING, serverSelectionTimeoutMS=MongoDB_Settings.MONGODB_CONN_TIMEOUT).server_info() else False
        except:
            if not can_force_start or MongoDB_Settings.MONGODB_ATLAS:
                raise Exception(f'ERROR - MongoDB ping failed for host [{MongoDB_Settings.MONGODB_CONNECTION_STRING}:{MongoDB_Settings.MONGODB_PORT if not MongoDB_Settings.MONGODB_ATLAS else ""}]. Ensure the service is running and config is correct')
            
            print(f'ERROR - MongoDB ping failed for host [{MongoDB_Settings.MONGODB_CONNECTION_STRING}:{MongoDB_Settings.MONGODB_PORT if not MongoDB_Settings.MONGODB_ATLAS else ""}]. Attempting to force start...')

            if not os.path.exists(f'{MongoDB_Settings.MONGODB_LOG_PATH}'): os.system(f'touch {MongoDB_Settings.MONGODB_LOG_PATH}')
            os.system(f'{MongoDB_Settings.MONGODB_INSTALLATION_PATH} --fork --logpath={MongoDB_Settings.MONGODB_LOG_PATH} --dbpath={MongoDB_Settings.MONGODB_DATA_PATH}')
            MongoDB_Settings.check_mongodb_connection()

            print('Done :)')