''' Builtin handler with default CRUD handling '''

# Base class
from ..api.main import RouteHandler

# Typing
from typing import Callable

class DefaultRouteHandler(RouteHandler):
    ''' Specifies the default logic to be used for all methods passed
    
        TODO - Explanation
    '''

    def __init__(self, GET:Callable=None, POST:Callable=None, DELETE:Callable=None, PUT:Callable=None, schema:dict=None):
        ''' Initialize a new handler for a route
        
        Args:

            GET (function): The function to call when a GET request is received. The function must accept the 
                `request` and `payload` argments. If a collection is specified, the `collection` argument must be 
                accepted as well

            POST (function): The function to call when a POST request is received. The function must accept the 
                `request` and `payload` argments. If a collection is specified, the `collection` argument must be 
                accepted as well
            
            DELETE (function): The function to call when a DELETE request is received. The function must accept the 
                `request` and `payload` argments. If a collection is specified, the `collection` argument must be 
                accepted as well
            
            PUT (function): The function to call when a PUT request is received. The function must accept the 
                `request` and `payload` argments. If a collection is specified, the `collection` argument must be 
                accepted as well
        '''
        
        if GET: self.GET = GET
        if POST: self.POST = POST
        if DELETE: self.DELETE = DELETE
        if PUT: self.PUT = PUT
        self.PATCH = None
        self.OPTIONS = None

        self.methods = list(filter(lambda x: getattr(self,x) != None, self.SUPPORTED_HTTP_METHODS))

        #TODO - JSONSCHEMA Support