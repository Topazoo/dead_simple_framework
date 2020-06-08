# Flask HTTP
from flask import request, Request, Response, jsonify

# API Errors
from .errors import API_Error

# API Utilities
from .utils import *

# Database
from ..database import Database

# Encoding
import json

# Utilities
import os

# TODO - [Useability]    | Authentication request/verification
# TODO - [Extendability] | Get debug settings from main app config, fallback on env

class API:
    ''' Internal HTTP requests handler for Flask routes '''

    ROUTES = {}

    @classmethod
    def HANDLER(cls):  # Supported auto-handling for routes
        return {'GET': cls.GET, 'POST': cls.POST, 'PUT': cls.PUT, 'DELETE': cls.DELETE}
    
    @staticmethod
    def GET(request:Request, database:str=None, collection:str=None) -> Response:
        ''' Fetch model data from the server or respond with the appropriate HTTP status code on error. 
        
            The request query string must supply the model's (class) name. It may also supply one or more optional 
            filter and sort parameters.
            --> request : The GET request sent to the server.
            <-- JSON containing the HTTP status code signifying the request's success or failure and
                a list of MongoDB records matching the supplied parameters if the request did not fail.
                GET Request Formats:
                    All - Get all records from a collection.
                        /api/
                        
                    Filtering - Get all records from a collection with field(s) matching the provided value(s).
                        /api/?filter=<<field>>:<<value>>
                        /api/?filter=<<field1>>:<<value1>>,<<field2>>:<<value2>>
                                                                            
                    Sorting - Get all records from a collection. sorted by the provieded field(s). 
                        /api/?sort=<<field>>
                        /api/?sort=<<field1>>,<<field2>>

                    Filtering + Sorting - Get all records from a collection with field(s) matching the provided 
                                        value(s) sorted by the provided field(s).
                        
                        /api/?filter=<<field1>>,<<field2>>:<<value>>&sort=<<field1>> 
                GET Response Format:
                    {"data": [JSON], "code": <<code>>}            
        '''
        
        try:
            # Parse the query string into key/value pairs and store
            payload = parse_query_string(request.query_string.decode()) if request.query_string.decode() else {}
            # Use the query string to send a database query
            data_cursor = fetch_and_filter_data(payload, database, collection)
            # Sort the data if one was specified in the query string
            sorted_data = list(sort_data(data_cursor, payload))

            return JsonResponse({'data': sorted_data}, 200 if len(sorted_data) > 0 else 404)
            
        except Exception as e:
            if os.environ.get('APP_ENV') == 'development':
                raise e

            return JsonError('GET', e)


    @staticmethod
    def POST(request:Request, database:str=None, collection:str=None) -> Response:
        ''' Create a new MongoDB record or respond with the appropriate HTTP status code on error. 
            
            --> request : The POST request sent to the server.
            <-- JSON containing the HTTP status code signifying the request's success or failure.
                POST Body Format:
                        { {<<field1>>: <<value1>>, <<field2>>: <<value2>>} }
                POST Response Format:
                    {"code": <<code>>}            
        '''

        try:
            # Get request body parameters
            payload = request.get_json(force=True) if request.data else {}
            # Remove any passed _id and insert in the database [TODO - allow? Maybe a config option?]
            if payload:
                payload.pop('_id', None)
                inserted_id = insert_data(payload, database, collection)
            else:
                raise API_Error('No data supplied to POST', 500)

            return JsonResponse({'_id': str(inserted_id)}, code=200)

        except Exception as e:
            if os.environ.get('APP_ENV') == 'development':
                raise e

            return JsonError('POST', e)


    @staticmethod
    def PUT(request:Request, database:str=None, collection:str=None) -> Response:
        ''' Update a MongoDB record or respond with the appropriate HTTP status code on error. 
            
            The request body must supply a dictionary of 
            one or more field/value pairs to update the record with, along with the ID of the record to update
            
            --> request : The PUT request sent to the server.
            <-- JSON containing the HTTP status code signifying the request's success or failure.
                PUT Body Format:
                    { 
                        "filter": {<<field1>>: <<value1>>, <<field2>>: <<value2>>},
                        "fields": {<<field1>>: <<value1>>, <<field3>>: <<value3>>} 
                    }
                PUT Response Format:
                    {"code": <<code>>}            
        '''

        try:
            # Get request body parameters
            payload = request.get_json(force=True) if request.data else {}
            # Use the passed _id to update data in the database
            if payload:
                _id = payload.get('_id')
                if not getattr(update_data(payload, database, collection), 'modified_count', None): 
                    raise API_Error(f'ID [{_id}] not found', 404)
            else:
                raise API_Error('No data supplied to PUT', 500)

            return JsonResponse(code=200)

        except Exception as e:
            if os.environ.get('APP_ENV') == 'development':
                raise e

            return JsonError('PUT', e)


    @staticmethod
    def DELETE(request:Request, database:str=None, collection:str=None) -> Response:
        ''' Delete a MongoDB record or respond with the appropriate HTTP status code on error. 
            
            The request body must supply the ID of the record to delete
            *The filter parameters must match only a single model*
            
            --> request : The DELETE request sent to the server.
            <-- JSON containing the HTTP status code signifying the request's success or failure.
                DELETE Body Format:
                    { "model": <<model>>, "filter": {<<field1>>: <<value1>>, <<field2>>: <<value2>>} }
                DELETE Response Format:
                    {"code": <<code>>}            
        '''

        try:
            # Get request body parameters
            payload = request.get_json(force=True) if request.data else {}
            if payload:
                # Use the passed _id to update data in the database
                _id = payload.get('_id')
                if not getattr(delete_data(payload, database, collection), 'deleted_count', None):
                    raise API_Error(f'ID [{_id}] not found', 404)
            else:
                raise API_Error('No data supplied to DELETE', 500)

            return JsonResponse(code=200)

        except Exception as e:
            if os.environ.get('APP_ENV') == 'development':
                raise e

            return JsonError('DELETE', e)


    @classmethod
    def _check_method(cls, url:str, method:str, route_config:dict):
        ''' Ensure the method is allowed for a route or raise a 405 error '''

        # If the method isn't listed in the route conig the user passed it isn't allowed
        if method not in route_config['methods']:
            raise API_Error(f'Method [{method}] not allowed for route [{url}]', 405)

        # If the method doesn't have a handler assigned it isn't allowed
        if method not in cls.HANDLER():
            raise API_Error(f'No hanlder for [{method}]', 405)


    @classmethod
    def main(cls) -> Response:
        ''' Called when the /api/ endpoint is sent an HTTP request. Delegates 
            to the appropriate handler based on the request method or returns a JSON
            formatted error if the method is not supported.
            --> request : The HTTP request sent to the server.
            <-- JSON containing the HTTP status code signifying the request's success or failure and
                all other data returned from the server.
        '''

        # Get the configuration for the route that was accessed
        route_config = cls.ROUTES[str(request.url_rule)]

        # Ensure the method is allowed
        cls._check_method(str(request.url_rule), request.method, route_config)

        # Get the database/collection
        database, collection = route_config.get('database'), route_config.get('collection')
        
        # Run CRUD handling
        data = cls.HANDLER()[request.method](request, database, collection)

        # Get the logic that should be run for this route (if any)
        delegate = route_config.get('logic')

        # Run it, or return the data for the CRUD operation run
        return data if not delegate else delegate(request, data)
