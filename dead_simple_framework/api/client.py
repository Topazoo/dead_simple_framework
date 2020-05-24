# Requests
import requests

# API Utilities
from .utils import create_query_string

# API Errors
from .errors import API_Client_Error


class API:
    ''' Client for making HTTP requests  '''

    @staticmethod
    def get(url:str, query_params:dict=None, ignore_errors=False):
        ''' [HTTP GET] Fetch a resource from an API '''

        # Format URL to send the request to
        url = f"{url}{create_query_string(query_params)}"

        # Send the request
        result = requests.get(url)

        # Check for errors
        if result.status_code != 200:
            if not ignore_errors:
                raise API_Client_Error(url, 'GET', result.status_code)
            return None

        return result


    @staticmethod
    def get_json(url:str, query_params:dict=None, ignore_errors=False) -> dict:
        ''' [HTTP GET] Fetch a JSON from an API '''

        # Get the raw result
        res = API.get(url, query_params, ignore_errors)

        # Extract data into dictionary
        return res.json() if res else {}
