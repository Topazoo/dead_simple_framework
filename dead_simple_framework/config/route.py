# Interface class
from .config import Config

# Schema manager
from .schema import SchemaHandler

class Route(Config):
    ''' Used to specify a route in the config dictionary '''

    CONFIG_TYPE = 'url'

    def __init__(self, url:str, handler=None, name:str=None, defaults:dict=None, collection:str=None, database:str=None, schema:dict=None):
        ''' Initialize a new route to add to the route config 
        
        Args:
        
            url (str): The url for this route

            handler (RouteHandler, optional): A `RouteHandler` class specifying the logic for this route. Defaults to the default handler

            defaults (dict, optional): Optional defaults for request body or query string parameters for this route
            
            collection (str, optional): Optional MongoDB collection to use for automatic storage and retrieval
                of data when a request is sent to the route. This allows automatic CRUD operations with no additional
                config. See the documentation for the internal API for more info (TODO)
            
            database (str, optional): Optional MongoDB database to use for automatic storage and retrieval
                of data when a request is sent to the route. This allows automatic CRUD operations with no additional
                config. If this is not set the default database is used. See the documentation for the internal API for more info (TODO)
        '''

        self.url = Config.normalize_url(url)
        self.name = self.url if not name else name
        self.defaults = defaults
        self.handler = handler
        self.collection = collection
        self.database = database
        self.schema_handler = SchemaHandler(schema)
