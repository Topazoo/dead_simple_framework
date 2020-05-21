if __package__ is None or __package__ == '':
    from utils import create_query_string
    from errors import API_Client_Error
else:
    from .utils import create_query_string
    from .errors import API_Client_Error

import requests


class API:
    ''' Internal API interface '''

    @staticmethod
    def get(url:str, query_params:dict=None):
        ''' [HTTP GET] Fetch a resource from an API '''

        url = f"{url}{create_query_string(query_params)}"
        result = requests.get(url)
        if result.status_code != 200:
            raise API_Client_Error(url, 'GET', result.status_code)

        return result


    @staticmethod
    def get_json(url:str, query_params:dict=None):
        ''' [HTTP GET] Fetch a JSON from an API '''

        return API.get(url, query_params).json()
