import redis, os, json

class Cache:
    ''' Client for caching task results or database queries '''

    def __init__(self):
        self._redis = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=os.environ.get('REDIS_PORT', 6379), db=0)


    def cache_string(self, key:str, value:str):
        ''' Add or update a key-value pair in the cache '''

        self._redis.set(key, value)


    def cache_dict(self, key:str, value:dict):
        ''' Add or update a dictionary in the cache '''

        self.cache_string(key, json.dumps(value)) # Serialize dictionaries for storage


    def cache_list(self, key:str, value:list):

        self.cache_dict(key, value) # Delegate works for this


    def get(self, key):
        ''' Fetch data from the cache by key '''

        result = self._redis.get(key).decode()

        # Attempt to automatically correct dictionary  and list typing
        if (result[0] == '{' and result[-1] == '}') or (result[0] == '[' and result[-1] == ']'):
            try:
                result = json.loads(result)
            except:
                pass
           
        return result
