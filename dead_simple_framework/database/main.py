# MongoDB
from bson.objectid import ObjectId
from pymongo.collection import Collection
from pymongo import TEXT
from werkzeug.local import LocalProxy
from pymongo.errors import OperationFailure

# MongoDB Settings
from ..config import MongoDB_Settings

# Utilities
from .utils import get_mongo_instance

# TODO - [Stability]     | Warnings + (Dummy `Database` if MongoDB isn't running)?
# TODO - [Useability]    | Allow `connect()` and `disconnect()` as class methods


class Database:
    ''' Client to store and retrieve dictionary data from the database '''

    # Default database/collection pulled from the environment but defaults to these
    CONNECTION = LocalProxy(get_mongo_instance)

    def __init__(self,database:str=None, collection:str=None):
        # For use with the context manager (`with` statement)
        self.database = database
        self.collection = collection


    def connect(self, database:str=None, collection:str=None) -> Collection:
        ''' Connect to a database and collection and return the collection

            - `database` defualts to the `MONGODB_DEFAULT_DB` setting if not passed

            - `collection` defualts to the `MONGODB_DEFAULT_COLLECTION` setting if not passed
        '''

        # Connect to the default database/collection if none passed
        if not database:   database   = MongoDB_Settings.MONGODB_DEFAULT_DB if not self.database else self.database
        if collection is None: collection = MongoDB_Settings.MONGODB_DEFAULT_COLLECTION if not self.collection else self.collection


        # Return the collection
        return self.CONNECTION.get_collection(collection)
    

    def disconnect(self):
        ''' Disconnect from a database and collection '''

        pass


    def __enter__(self) -> Collection:
       return self.connect()
       

    def __exit__(self, exception_type, exception_value, traceback):
        self.disconnect()


    @classmethod
    def register_indices(cls, indices):
        ''' Create user specified indices in MongoDB '''

        curr_indices = indices.INDICES.copy()
        for collection,indices in curr_indices.items():
            compounds = [index.compound_with for index in indices.values() if index.compound_with]
            with cls(collection=collection) as coll:
                try:
                    for field, index in indices.items():
                        if index.is_text:
                            coll.create_index([(field, TEXT)])
                        elif field not in compounds and not index.compound_with:
                            coll.create_index([(field, index.order)], **index.properties, background=True)
                        elif field not in compounds:
                            if index.compound_with not in indices:
                                raise TypeError(f'Index [{index.compound_with}] to compound with index [{field}] not specified for collection [{collection}]!')

                            compound = indices[index.compound_with]
                            index.properties.update(compound.properties)
                            coll.create_index([(field, index.order), (compound.field, compound.order)], **index.properties, background=True)

                except OperationFailure as e:
                    if e.code == 85:
                        pass
                    else:
                        raise e

    @classmethod
    def register_fixtures(cls, fixtures):
        ''' Register database fixtures in MongoDB'''

        fixtures = fixtures.fixtures
        for collection in fixtures:
            with cls(collection=collection) as coll:
                for fixture in fixtures[collection]:
                    fixture["_id"] = ObjectId(fixture["_id"])
                    coll.update_one({"_id": fixture["_id"]}, {"$set": fixture}, upsert=True)
