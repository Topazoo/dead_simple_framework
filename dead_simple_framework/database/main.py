# MongoDB
from pymongo import MongoClient
from pymongo.collection import Collection

# Utilities
import os


class Database:
    # TODO - This can be made more static

    ''' Client to store and retrieve dictionary data from the database '''

    # Default database/collection pulled from the environment but defaults to these
    DEFAULT_DB = os.environ.get('MONGODB_DEFAULT_DB', 'db')
    DEFAULT_COLLECTION = os.environ.get('MONGODB_DEFAULT_COLLECTION', 'data')
    CONNECTION = None

    def __init__(self,database:str=None, collection:str=None):
        # For use with the context manager (`with` statement)
        self.database = database
        self.collection = collection


    def _get_host(self) -> str:
        ''' Connection string for MongoDB '''

        # TODO - Allow config from dictionary

        auth_str = os.environ.get('MONGODB_HOSTNAME', 'localhost')
        if os.environ.get('MONGODB_USERNAME') and os.environ.get('MONGODB_PASSWORD'):
            auth_str = f"{os.environ.get('MONGODB_USERNAME')}:{os.environ.get('MONGODB_PASSWORD')}@" + auth_str

        return auth_str


    def connect(self, database:str=None, collection:str=None) -> Collection:
        ''' Connect to a database and collection and return the collection

            - `database` defualts to the `MONGODB_DEFAULT_DB` environmental variable if not passed

            - `collection` defualts to the `MONGODB_DEFAULT_COLLECTION` environmental variable if not passed
        '''

        # Connect to the default database/collection if none passed
        if not database:   database   = os.environ.get('MONGODB_DEFAULT_DB', 'db') if not self.database else self.database
        if not collection: collection = os.environ.get('MONGODB_DEFAULT_COLLECTION', 'data') if not self.collection else self.collection

        # If a connection to the client isn't open, open one
        if not self.CONNECTION:
            self.CONNECTION = MongoClient(f'mongodb://{self._get_host()}:27017/')

        # Return the collection
        return self.CONNECTION.get_database(database).get_collection(collection)
    

    def disconnect(self):
        ''' Disconnect from a database and collection '''

        if self.CONNECTION:
            self.CONNECTION.close()
            self.CONNECTION = None


    def __enter__(self) -> Collection:
       return self.connect()
       
    def __exit__(self, exception_type, exception_value, traceback):
        self.disconnect()
    

