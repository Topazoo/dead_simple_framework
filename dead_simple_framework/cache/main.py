# Redis
import redis

# Redis Errors
from redis.exceptions import ResponseError, DataError

# Encoding
from ..encoder import JSON_Encoder
import json

# Utilities
import os


class Cache:
    ''' Client for caching task results or database queries '''

    # TODO - Dynamic list support

    def __init__(self):
        # Connect to Redis
        self._redis = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=os.environ.get('REDIS_PORT', 6379), db=0)


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


    def cache_dynamic_dict(self, key, value:dict):
        ''' Store a python dictionary as a hash. Allows dictionary values to be updated without fetching the stored value '''

        # Attempt to insert the raw dictionary in Redis
        try:
            self._redis.hset(key, mapping=value)

        # Serialize the inner contents if necessary
        except DataError:
            value = {x: json.dumps(y, cls=JSON_Encoder) for x,y in value.items()}
            self._redis.hset(key, mapping=value)


    def get_dynamic_dict_value(self, dict_key, key):
        ''' Get a value from a cached dictionary stored with cache_dynamic_dict() '''

        # Retrieve the dynamically cached dictionary
        result = self._redis.hget(dict_key, key)

        # Correct the type using `json.loads()` if necessary
        if result:
            return self._fix_type(result).decode()


    def get(self, key):
        ''' Fetch data from the cache by key '''

        # Retrieve the cached value and fix type if necessary
        try:
            return self._fix_type(self._redis.get(key).decode())

        # Attempt to retrieve a dynamically cached dictionary on failure
        except ResponseError: 
            return {x.decode(): self._fix_type(y.decode()) for x,y in  self._redis.hgetall(key).items()}


    def _fix_type(self, result):
        ''' Attempt to reconstruct the result type '''

        # Attempt to automatically correct dictionary  and list typing
        if (result[0] == '{' and result[-1] == '}') or (result[0] == '[' and result[-1] == ']'):
            try:
                result = json.loads(result)
            except:
                pass
           
        return result
