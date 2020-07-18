
# Interface class
from .config import Config

# Typing
from typing import Callable


class Route(Config):
    ''' Used to specify a route in the config dictionary '''

    SUPPORTED_HTTP_METHODS = ['GET', 'POST', 'DELETE', 'PUT', 'PATCH', 'OPTIONS']
    CONFIG_TYPE = 'url'

    def __init__(self, url:str, name:str=None, methods:list=['GET'], defaults:dict=None, logic:Callable=None, collection:str=None):
        ''' Initialize a new route to add to the route config 
        
        Args:
            url (str): The url for this route
            methods (list): The supported methods for this route (must be included in `SUPPORTED_HTTP_METHODS`).
                Defaults to ['GET']
            defaults (dict, optional): Optional defaults for request body or query string parameters for this route
            logic (Callable, optional): Optional function to run when a request is made to this route.
                receives the query string or body params with any defaults if they were passed
            collection (str, optional): Optional MongoDB collection to use for automatic storage and retrieval
                of data when a request is sent to the route. This allows automatic CRUD operations with no additional
                config. See the documentation for the internal API for more info (TODO)
        '''

        self.url = Config.normalize_url(url)
        self.name = self.url if not name else name
        self.methods = self._validate_methods(methods)
        self.defaults = defaults
        self.logic = logic
        self.collection = collection


    def _validate_methods(self, methods:list):
        ''' Ensure passed methods are part of `SUPPORTED_HTTP_METHODS` '''

        unsupported_methods = list(set(methods) - set(self.SUPPORTED_HTTP_METHODS))
        assert not unsupported_methods, f"{self.__class__.__name__} was initialized with unsupported `methods` argument. HTTP methods {unsupported_methods} are not supported"        
        return methods
