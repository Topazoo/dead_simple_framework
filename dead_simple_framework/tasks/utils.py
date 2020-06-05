''' Shared utility functions for task result storage/caching '''

# Database
from ..database import Database
from bson import ObjectId

# Cache
from ..cache import Cache


def cache_mongo_id(_id:ObjectId, cache_key:str, cache_sub_key:str=None):
    ''' Cache the ID of persistently stored data '''

    Cache().cache_dynamic_dict(cache_key, {cache_sub_key: str(_id)}) if cache_sub_key else Cache().cache_string(cache_key, str(_id))


def insert_persistently_and_cache(collection:str, cache_key:str, document:dict, cache_sub_key=None):
    ''' Store data persistently in the database and make it easily available via the cache '''

    with Database(collection=collection) as db:
        cache_mongo_id(db.insert_one(document).inserted_id, cache_key, cache_sub_key)


def upsert_persistently_and_cache(collection:str, cache_key:str, document:dict, cache_sub_key=None):
    ''' Update data stored persistently or insert if no data stored '''

    cache = Cache()
    if cache_sub_key:
        _id = cache.get_dynamic_dict_value(cache_key, cache_sub_key) or ObjectId()
    else:
        _id = cache.get(cache_key) or ObjectId()

    with Database(collection=collection) as db:
        db.delete_one({'_id': ObjectId(_id)})
        cache_mongo_id(db.insert_one(document).inserted_id, cache_key, cache_sub_key)
