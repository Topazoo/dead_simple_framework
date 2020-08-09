# Redis
import redis

# Redis Settings
from ..config import Redis_Settings

# Redis Errors
from redis.exceptions import ResponseError, DataError

# Encoding
from ..encoder import JSON_Encoder
import json

# Utilities
import os

# Typing
from typing import Union

# TODO - [Stability]     | Dummy cache if Redis not running
# TODO - [Stability]     | Timeouts + Automatic retries
# TODO - [Useability]    | Allow serialization/deserialization and storage of typed data
# TODO - [Useability]    | Support for lists (queues)

class Cache:
    ''' Client for caching task results or database queries '''

    def __init__(self):
        # Connect to Redis
        self._redis = redis.Redis(host=Redis_Settings.REDIS_HOST, port=Redis_Settings.REDIS_PORT, db=Redis_Settings.REDIS_DB)


    def cache_string(self, key:str, value:str):
        ''' Add or update a key-value pair in the cache '''

        self._redis.set(key, value)


    def cache_dict(self, key:str, value:dict):
        ''' Add or overwrite a dictionary in the cache '''

        # Serialize dictionary then store
        self.cache_string(key, json.dumps(value, cls=JSON_Encoder)) 


    def cache_list(self, key:str, value:list):
        ''' Add or overwrite a list in the cache '''

        # Serialize the list with `json.dumps()` and store
        self.cache_dict(key, value)


    def cache_dynamic_dict(self, key:str, value:dict):
        ''' Store a python dictionary as a hash. Allows dictionary values to be updated without fetching the stored value '''

        # Attempt to insert the raw dictionary in Redis
        try:
            self._redis.hset(key, mapping=value)

        # Serialize the inner contents if necessary
        except DataError:
            value = {x: json.dumps(y, cls=JSON_Encoder) for x,y in value.items()}
            self._redis.hset(key, mapping=value)


    def get_dynamic_dict_value(self, dict_key:str, key:str) -> str:
        ''' Get a value from a cached dictionary stored with cache_dynamic_dict() '''

        # Retrieve the dynamically cached dictionary
        result = self._redis.hget(dict_key, key)
        
        if result:
            return result.decode()


    def clear_dynamic_dict_value(self, dict_key:str, key:Union[list,str]):
        ''' Delete a key or list of keys from a cached dictionary stored with cache_dynamic_dict() '''

        self._redis.hdel(dict_key, *([key] if isinstance(key,str) else key))


    def get(self, key:str) -> str:
        ''' Fetch data from the cache by key '''

        # Retrieve the cached value and fix type if necessary
        try:
            return self._redis.get(key).decode()

        # Attempt to retrieve a dynamically cached dictionary on failure
        except ResponseError: 
            return {x.decode(): y.decode() for x,y in  self._redis.hgetall(key).items()}


    def remove(self, key:Union[list,str]):
        ''' Remove a stored key or list of keys '''

        self._redis.delete(*([key] if isinstance(key,str) else key))


    def keys(self, regex:str='*') -> list:
        ''' View the keys stored in the cache or all keys matching a passed regular expression'''

        return [k.decode() for k in self._redis.keys(regex)]


    def view(self, regex:str='*') -> dict:
        ''' View the entire contents of the cache or the keys+contents matching a passed regular expression '''
        
        return {k:self.get(k) for k in self.keys(regex)}


    def flush(self, force=False):
        ''' Flush the cache '''

        self._redis.flushall(asynchronous=(not force))


    def save_to_disk(self):
        ''' Force-save the cache to disk '''

        self._redis.save()
        