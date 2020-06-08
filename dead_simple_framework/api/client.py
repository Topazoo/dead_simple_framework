# Requests
import requests

# API Utilities
from .utils import create_query_string

# API Errors
from .errors import API_Client_Error

# Utilities
from time import sleep


class API:
    ''' Client for making HTTP requests  '''

    HEADERS = {"User-Agent": "Mozilla/5.0"}

    @classmethod
    def send_request(cls, method:str, url:str, query_params:dict=None, data:dict=None, ignore_errors=False, retry_ms=500, num_retries=3):
        ''' Shared logic that handles actually firing a request '''

        # Format the URL
        url = f"{url}{create_query_string(query_params)}".strip()

        # Open a session
        with requests.Session() as session:
            # Try the request up to `num_retries` times
            for x in range(0, num_retries):
                result = session.send(session.prepare_request(requests.Request(method, url, headers=cls.HEADERS)))

                # If there is a result
                if result:
                    # If the status code is not 200, the result may be incorrect
                    if result.status_code != 200:
                        if not ignore_errors:
                            raise API_Client_Error(url, method, result.status_code)

                    # Check for actual result data and return if present
                    if result.text:
                        return result

                # Otherwise wait, then rety
                sleep(retry_ms/1000)
        
        return result if result.text else None


    @classmethod
    def options(cls, url:str, query_params:dict=None, data:dict=None, ignore_errors=False, retry_ms=500, num_retries=3):
        ''' [HTTP OPTIONS] Send an options request '''

        return cls.send_request('OPTIONS', url, query_params=query_params, data=data, ignore_errors=ignore_errors, retry_ms=retry_ms, num_retries=num_retries)


    @classmethod
    def post(cls, url:str, query_params:dict=None, data:dict=None, ignore_errors=False, retry_ms=500, num_retries=3):
        ''' [HTTP POST] Send data to an API'''

        return cls.send_request('POST', url, query_params=query_params, data=data, ignore_errors=ignore_errors, retry_ms=retry_ms, num_retries=num_retries)


    @classmethod
    def put(cls, url:str, query_params:dict=None, data:dict=None, ignore_errors=False, retry_ms=500, num_retries=3):
        ''' [HTTP PUT] Replace data via API'''

        return cls.send_request('PUT', url, query_params=query_params, data=data, ignore_errors=ignore_errors, retry_ms=retry_ms, num_retries=num_retries)


    @classmethod
    def patch(cls, url:str, query_params:dict=None, data:dict=None, ignore_errors=False, retry_ms=500, num_retries=3):
        ''' [HTTP PATCH] Update data via API'''

        return cls.send_request('PATCH', url, query_params=query_params, data=data, ignore_errors=ignore_errors, retry_ms=retry_ms, num_retries=num_retries)


    @classmethod
    def get(cls, url:str, query_params:dict=None, ignore_errors=False, retry_ms=500, num_retries=3):
        ''' [HTTP GET] Fetch a resource from an API '''

        return cls.send_request('GET', url, query_params=query_params, ignore_errors=ignore_errors, retry_ms=retry_ms, num_retries=num_retries)


    @classmethod
    def get_json(cls, url:str, query_params:dict=None, ignore_errors=False, retry_ms=500, num_retries=3) -> dict:
        ''' [HTTP GET] Fetch a JSON from an API '''

        # Get the raw result
        res = cls.get(url, query_params, ignore_errors, retry_ms, num_retries)

        # Extract data into dictionary
        return res.json() if res else {}

