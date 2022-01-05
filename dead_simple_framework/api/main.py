# Flask HTTP
from dead_simple_framework.slack import Slack
from flask import request, Request, Response

# App Settings
from ..config import App_Settings, Sentry_Settings, Slack_Settings

# API Errors
from .errors import API_Error

# Database
from ..database import Database

# Route object
from ..config import Route

# Utils
from .utils import *

# Typing
from typing import Callable, Dict
from pymongo.collection import Collection

# Exceptions
from sentry_sdk import capture_exception
import traceback, logging


class RouteHandler:
    ''' Internal HTTP requests handler for Flask routes '''

    ROUTES:Dict[str, Route] = {}
    SUPPORTED_HTTP_METHODS = ['GET', 'POST', 'DELETE', 'PUT', 'PATCH', 'OPTIONS']
    VERIFIER_FAILED_MESSAGE = 'Payload verification failed. Ensure data is correct and try again'

    def __init__(self, GET:Callable=None, POST:Callable=None, DELETE:Callable=None, PUT:Callable=None, PATCH:Callable=None, OPTIONS:Callable=None, verifier:Callable=None):
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
            
            PATCH (function): The function to call when a PATCH request is received. The function must accept the 
                `request` and `payload` argments. If a collection is specified, the `collection` argument must be 
                accepted as well

            OPTIONS (function): The function to call when a OPTIONS request is received. The function must accept the 
                `request` and `payload` argments. If a collection is specified, the `collection` argument must be 
                accepted as well

            verifier (function): The function to check the contents of the payload. Should return True if the payload is valid or False if not
        '''

        self.GET = GET
        self.POST = POST
        self.DELETE = DELETE
        self.PUT = PUT
        self.PATCH = PATCH
        self.OPTIONS = OPTIONS

        if verifier: self.verifier = verifier
        self.methods = list(filter(lambda x: getattr(self,x) != None, self.SUPPORTED_HTTP_METHODS))


    @staticmethod
    def verifier(method:str, payload:dict, identity:dict) -> bool:
        ''' Arbitrary logic that can be specified by the user to validate the payload received by an endpoint
            
            Args:

                method (str): The method that the endpoint was accessed with

                payload (dictionary): The payload received at the endpoint

                identity (dictionary): The JWT identity received determined the endpoint
        
        '''

        return True


    @staticmethod
    def GET(request:Request, payload:dict, collection:Collection) -> Response:
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
            # Use the query string to send a database query
            data_cursor = fetch_and_filter_data(payload, collection, lazy=True)
            # Sort the data if one was specified in the query string
            sorted_data = sort_data(data_cursor, payload)
            # Limit the data if a limit was specified in the payload
            limited_data = limit_data(sorted_data, payload)

            data = list(limited_data)
            
            return JsonResponse({'data': data}, 200 if len(data) > 0 else 404)
            
        except API_Error as e:
            return JsonException('GET', e)

        except Exception as e:
            if App_Settings.APP_ENV == 'development': raise e
            return JsonException('GET', e)


    @staticmethod
    def POST(request:Request, payload, collection:Collection) -> Response:
        ''' Create a new MongoDB record or respond with the appropriate HTTP status code on error. 
            
            --> request : The POST request sent to the server.
            <-- JSON containing the HTTP status code signifying the request's success or failure.
                POST Body Format:
                        { {<<field1>>: <<value1>>, <<field2>>: <<value2>>} }
                POST Response Format:
                    {"code": <<code>>}            
        '''

        try:
            # Remove any passed _id and insert in the database [TODO - allow? Maybe a config option?]
            if payload:
                payload.pop('_id', None)
                inserted_id = insert_data(payload, collection)
            else:
                raise API_Error('No data supplied to POST', 500)

            return JsonResponse({'_id': str(inserted_id)}, code=200)

        except API_Error as e:
            return JsonException('POST', e)

        except Exception as e:
            if App_Settings.APP_ENV == 'development': raise e
            return JsonException('POST', e)


    @staticmethod
    def PUT(request:Request, payload:dict, collection:Collection) -> Response:
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
            # Use the passed _id to update data in the database
            if payload:
                _id = payload.get('_id')
                if not update_data(payload, collection): 
                    raise API_Error(f'ID [{_id}] not found', 404)
            else:
                raise API_Error('No data supplied to PUT', 500)

            return JsonResponse({'success': True}, code=200)

        except API_Error as e:
            return JsonException('PUT', e)

        except Exception as e:
            if App_Settings.APP_ENV == 'development': raise e
            return JsonException('PUT', e)


    @staticmethod
    def DELETE(request:Request, payload:dict, collection:Collection) -> Response:
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
            if payload:
                # Use the passed _id to update data in the database
                _id = payload.get('_id')
                if not delete_data(payload, collection):
                    raise API_Error(f'ID [{_id}] not found', 404)
            else:
                raise API_Error('No data supplied to DELETE', 500)

            return JsonResponse({'success': True}, code=200)

        except API_Error as e:
            return JsonException('DELETE', e)

        except Exception as e:
            if App_Settings.APP_ENV == 'development': raise e
            return JsonException('DELETE', e)


    @staticmethod
    def _get_handler(method:str, route:Route) -> Callable:
        ''' Get the handler for the request on a given route or raise a 405 error '''

        handler = getattr(route.handler, method, None)

        # If the method isn't listed in the route config handler the user passed, it isn't allowed
        if not handler:
            raise API_Error(f'Method [{method}] not allowed for route [{route.url}]', 405)

        return handler

    
    @staticmethod
    def _check_logic(route_name:str, logic_func:Callable, collection:str):
        ''' Ensure user defined logic '''

        num_parameters = len(logic_func.__code__.co_varnames)

        if collection is not None and num_parameters < 3:
            raise API_Error(f'Handler [{logic_func.__name__}] for route [{route_name}] supports [{num_parameters}] arguments. Must support 3 (request, payload, collection)', 500)
        elif num_parameters < 2:
            raise API_Error(f'Handler [{logic_func.__name__}] for route [{route_name}] supports [{num_parameters}] arguments. Must support 2 (request, payload)', 500)
        

    @classmethod
    def main(cls) -> Response:
        ''' Called when the speciied endpoint is sent an HTTP request. Delegates 
            to the appropriate handler based on the request method or returns a JSON
            formatted error if the method is not supported.
            --> request : The HTTP request sent to the server.
            <-- JSON containing the HTTP status code signifying the request's success or failure and
                all other data returned from the server.
        '''
        payload = None
        try:
            # Get the configuration for the route that was accessed
            route = cls.ROUTES[str(request.url_rule)]

            # Get the logic for the request if the method is allowed
            logic = cls._get_handler(request.method, route)

            # Normalize query params
            if str(request.method) == 'GET':
                payload = parse_query_string(request.query_string.decode()) if request.query_string.decode() else {}
            else:
                payload = request.get_json(force=True) if request.data else dict(request.form)

            # Ensure user defined logic can accept required arguments or throw a warning
            cls._check_logic(route.name, logic, route.collection)

            # Ensure the payload passes schema validation
            validation_error = route.schema_handler.validate_request(request.url_rule, request.method, payload)
            if validation_error:
                return JsonResponse(validation_error, 400)

            # Ensure the payload passes the route verifier
            if getattr(route.handler, 'verifier', None) and not route.handler.verifier(request.method, payload, None): 
                raise API_Error(cls.VERIFIER_FAILED_MESSAGE, 400)

            # If a collection is specified, pass through to next function, otherwise just pass the request
            if route.collection or route.database:
                with Database(database=route.database, collection=route.collection) as collection:
                    response = logic(request, payload, collection)
                    return route.schema_handler.redact_response(request.method, JsonResponse(response) if not isinstance(response, Response) else response)

            response = logic(request, payload)
            return route.schema_handler.redact_response(request.method, JsonResponse(response) if not isinstance(response, Response) else response)

        # Catch errors handling API requests
        except API_Error as e:
            # If the error is not a 404
            if e.code != 404:

                # Log error to Sentry if it's enabled
                if Sentry_Settings.USE_SENTRY and Sentry_Settings.APP_SENTRY_HOST and Sentry_Settings.APP_SENTRY_SLUG:
                    capture_exception(e)

                # Log error to Slack if it's enabled
                if Slack_Settings.USE_SLACK and Slack_Settings.APP_SLACK_TOKEN:
                    Slack().log_api_exception(e, endpoint=request.url_rule, payload=payload or {})

                # Log error standard out
                logging.critical(f'API_Error: {e}')
                
            return JsonError(e.message, e.code)

        except Exception as e:

            # Log error to Sentry if it's enabled
            if Sentry_Settings.USE_SENTRY and Sentry_Settings.APP_SENTRY_HOST and Sentry_Settings.APP_SENTRY_SLUG:
                capture_exception(e)

            # Log error to Slack if it's enabled
            if Slack_Settings.USE_SLACK and Slack_Settings.APP_SLACK_TOKEN:
                Slack().log_exception(e, endpoint=request.url_rule, payload=payload or {})

            # Log error to standard out
            logging.critical(f'{type(e).__name__}: {e}')

            return JsonError({'error': str(e), 'traceback': str(traceback.format_exc()), 'code': 500}, 500)
