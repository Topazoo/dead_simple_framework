from redis.exceptions import ResponseError, DataError
import redis, os, json

class Cache:
    ''' Client for caching task results or database queries '''

    def __init__(self):
        self._redis = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=os.environ.get('REDIS_PORT', 6379), db=0)


    def cache_string(self, key:str, value:str):
        ''' Add or update a key-value pair in the cache '''

        self._redis.set(key, value)


    def cache_dict(self, key:str, value:dict):
        ''' Add or overwrite a dictionary in the cache '''

        self.cache_string(key, json.dumps(value)) # Serialize dictionaries for storage


    def cache_list(self, key:str, value:list):
        ''' Add or overwrite a list in the cache '''

        self.cache_dict(key, value) # Delegation to json.dumps() works for this


    def cache_dynamic_dict(self, key, value:dict):
        ''' Store a python dictionary as a hash. Allows dictionary values to be updated without fetching the stored value '''

        try: # Attempt to insert
            self._redis.hset(key, mapping=value)
        except DataError: # Serialize value if necessary
            value = {x: json.dumps(y) for x,y in value.items()}
            self._redis.hset(key, mapping=value)


    # TODO - Dynamic list support

    def get_dynamic_dict_value(self, dict_key, key):
        ''' Get a value from a cached dictionary stored with cache_dynamic_dict() '''

        return self._fix_type(self._redis.hget(dict_key, key).decode())


    def get(self, key):
        ''' Fetch data from the cache by key '''

        try: # Attempt to retrieve simple key (as string)
            return self._fix_type(self._redis.get(key).decode())
        except ResponseError: # Attempt to retrieve a hashed value
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
