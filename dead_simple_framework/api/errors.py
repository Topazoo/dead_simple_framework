# Storage Utilities
from collections import defaultdict

# Encoding
from json import dumps

class API_Error(Exception):
    ''' Error thrown by the server API when a bad request is received '''
    
    def __init__(self, message, code):
        super(Exception, self).__init__(message)
        self.message = message
        self.code = code

    def to_response(self):
        return dumps({
            'error': self.message,
            'code': self.code
        })


class API_Client_Error(Exception):
    ''' Error thrown by the API client when an error is received '''

    # TODO - Full list of HTTP error codes
    CODES = defaultdict(lambda: 'Unknown', {
        404: 'Resource Not Found',
        403: 'Forbidden - Ensure proper credentials were supplied',
        405: 'Not supported - The method is not supported',
        500: 'Server Error - The endpoint encountered an error processing the request'
    })
    
    
    def __init__(self, url:str, method:str, code:int):
        super(Exception, self).__init__(f"{method} Request Error [{code}] | {self.CODES[code]} | {url}")
        self.code = code
        self.method = method
