from redis.exceptions import ResponseError
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

        self.cache_dict(key, value) # Delegate works for this


    def cache_dynamic_dict(self, key, value:dict):
        ''' Store a python dictionary as a hash. Allows dictionary values to be updated without fetching the stored value '''

        self._redis.hset(key, mapping=value)


    # TODO - Dynamic list support
    

    def get(self, key):
        ''' Fetch data from the cache by key '''

        try: # Attempt to retrieve simple key (as string)
            result = self._redis.get(key).decode()
        except ResponseError as e: # Attempt to retrieve a hashed value
            return {x.decode(): y.decode() for x,y in  self._redis.hgetall(key).items()}

        # Attempt to automatically correct dictionary  and list typing
        if (result[0] == '{' and result[-1] == '}') or (result[0] == '[' and result[-1] == ']'):
            try:
                result = json.loads(result)
            except:
                pass
           
        return result

c = Cache()
c.cache_dynamic_dict('tests', {'one': 'id', 'two': 'id2'})
c.cache_dynamic_dict('tests', {'three': 'id', 'four': 'id2'})
print(c.get('tests')['three'])