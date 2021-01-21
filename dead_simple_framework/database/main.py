# MongoDB
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import OperationFailure

# MongoDB Settings
from ..config import App_Settings, MongoDB_Settings

# Utilities
import os

# TODO - [Stability]     | Warnings + (Dummy `Database` if MongoDB isn't running)?
# TODO - [Stability]     | Timeouts + Automatic retries
# TODO - [Extendability] | Initial indexes, host and other config from main app config
# TODO - [Useability]    | Allow `connect()` and `disconnect()` as class methods

class Database:
    ''' Client to store and retrieve dictionary data from the database '''

    # Default database/collection pulled from the environment but defaults to these
    CONNECTION = None

    def __init__(self,database:str=None, collection:str=None):
        # For use with the context manager (`with` statement)
        self.database = database
        self.collection = collection


    @classmethod
    def register_indices(cls, indices=None):
        ''' Create user specified indices in MongoDB '''

        indices = indices or {} # TODO - ALLOW IN SETTINGS
        if App_Settings.APP_USE_JWT:
            indices['_jwt_tokens'] = [{'indices': [('modified_on', -1)], 'expireAfterSeconds':10}]

        for coll,index_list in indices.items():
            with cls(collection=coll) as collection:
                try:
                    [collection.create_index(index.pop('indices'), **index) for index in index_list]
                except OperationFailure as e:
                    if e.code == 85:
                        pass
                    else:
                        raise e


    def connect(self, database:str=None, collection:str=None) -> Collection:
        ''' Connect to a database and collection and return the collection

            - `database` defualts to the `MONGODB_DEFAULT_DB` setting if not passed

            - `collection` defualts to the `MONGODB_DEFAULT_COLLECTION` setting if not passed
        '''

        # Connect to the default database/collection if none passed
        if not database:   database   = MongoDB_Settings.MONGODB_DEFAULT_DB if not self.database else self.database
        if not collection: collection = MongoDB_Settings.MONGODB_DEFAULT_COLLECTION if not self.collection else self.collection

        # If a connection to the client isn't open, open one
        if not self.CONNECTION: self.CONNECTION = MongoClient(MongoDB_Settings.MONGODB_CONNECTION_STRING)

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
