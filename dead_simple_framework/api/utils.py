# Flask HTTP
from flask import jsonify, Response

# API Errors
from .errors import API_Error

# Database
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from bson import ObjectId

# Typing
from typing import Union

# Debug
import logging


def JsonResponse(content: dict = {}, code: int = 200) -> dict:
    ''' Format an API JSON response.
        --> content [dict] : A dictionary of JSON serializable objects to return. Optional.
        
        --> code [int]: The HTTP status code to return. Optional.
        
        <-- The JSON formatted response. { <<content>>, "code": <<code>> }
    '''

    content['code'] = code
    
    return content


def JsonError(content: Union[dict, str] = {}, code: int = 500) -> dict:
    ''' Format an API JSON response.
        --> content [dict or str] : A dictionary of JSON serializable objects to return or an error message. Optional.
        
        --> code [int]: The HTTP status code to return. Optional.
        
        <-- The JSON formatted response. { <<content>>, "code": <<code>> }
    '''

    if isinstance(content, str): content = {'error': content}
    content['code'] = code
    
    return content


def JsonException(method: str, exception: Exception) -> dict:
    ''' Format an API JSON exception response.
        --> method : The HTTP request method that generated the error (e.g. POST).
        
        --> exception : The error generated.
        
        <-- A JSON formatted error response : { "msg" <<error_message>>, "code": <<code>> }.
    '''

    error_msg = '{} - {}'.format(method, str(exception)) 
    error_code = exception.code if type(exception) == API_Error else 500
    
    logging.critical(error_msg)

    raise API_Error(error_msg, code=error_code)


def parse_query_pairs(payload: str) -> dict:
    ''' Parse out one or more key/value pairs from a query string
        (e.g. /api/?param=key:value || /api/?param=key1:value1,key2:value2).
    
        --> payload : The arguments supplied with the parameter (The key value pairs in string form).
        <-- The parsed key/value pairs.
    '''

    pairs = {}
    for pair_tuple in map(lambda pair: pair.split(':'), [pair for pair in payload.split(',')]):
        pairs[normalize_query_string(pair_tuple[0])] = normalize_query_string(pair_tuple[1])

    return pairs


def parse_query_params(payload: str) -> list:
    ''' Parse out one or more parameter values pairs from a query string
        (e.g. /api/?param=value || /api/?param=value1,value2).
    
        --> payload : The arguments supplied with the parameter (The values in string form).
        <-- The parsed values.
    '''

    return [(normalize_query_string(value), 1) for value in payload.split(',')]


def normalize_query_string(raw_value:str) -> str:
    ''' Replace encoded keys and value characters in passed query params '''

    return raw_value.replace('%20', ' ')


def parse_query_string(payload: str) -> dict:
    ''' Parse out the filter and sort from a query string
    
        --> payload : The arguments supplied with the parameter (The values in string form).
        <-- The parsed values.
    '''

    dict_payload = {}
    query_params = payload.split('&')
    for param in query_params:
        args = param.split('=')
        if args[0] == 'filter':
            dict_payload[args[0]] = parse_query_pairs(args[1])
        elif args[0] == 'sort':
            dict_payload[args[0]] = parse_query_params(args[1])
        else:
            dict_payload[args[0]] = normalize_query_string(args[1])
        
    return dict_payload


def create_query_string(query_params:dict) -> str:
    ''' Generate a query string from a dictionary of parameters 

        e.g. {'item': '56', 'type': '21' }  -> "?item=56&type=21"
    '''

    return '?' + '&'.join([f"{k}={v}" for k,v in query_params.items()]) if query_params else ''


def fetch_and_filter_data(request_params: dict, collection:Collection, lazy=False) -> list:
    ''' Fetch records from the database matching a filter supplied in an HTTP request.
        Ensure fields supplied in the filter exist for the model. If no filter is supplied
        all objects are retrived.
    
        --> request_params : The parameters sent with the request (in querystring or body).
        <-- A list containing the MongoDB data matching the supplied filter or all objects in a collection.
    '''

    if not collection: raise API_Error('No collection was specified to get data from for this route! Check your Route configuration', 500)

    mongo_filter = request_params.get('filter') or request_params
    if '_id' in mongo_filter: mongo_filter['_id'] = ObjectId(mongo_filter['_id'])
    if request_params.get('sort'):
        [mongo_filter.update({s[0]: {'$exists': True}}) for s in request_params.get('sort')]

    res = collection.find(mongo_filter)
    return list(res) if not lazy else res
    

def sort_data(data: Cursor, request_params: dict) -> list:
    ''' Sorts a data according to the parameters sent in an HTTP request.
        --> data : The cursor of data to apply the sort to.
        --> request_params : The parameters sent with the request (in querystring or body).
        <-- A queryset containing the sorted data.
    '''

    mongo_sort = request_params.get('sort', {})
    if mongo_sort != {}:
        return data.sort(mongo_sort)
    
    return data


def insert_data(request_params: dict, collection:Collection) -> str:
    ''' Add data to the collection with the parameters sent in an HTTP request.
        --> request_params [dict] : The parameters sent with the request (in querystring or body).
        <-- [str] The ObjectId of the inserted data
    '''

    if not collection: raise API_Error('No collection was specified to insert data for this route! Check your Route configuration', 500)

    mongo_fields = request_params.copy()
    return str(collection.insert_one(mongo_fields).inserted_id)


def update_data(request_params: dict, collection:Collection, upsert:bool=False) -> bool:
    ''' Add data to the collection with the parameters sent in an HTTP request.
        --> request_params [dict] : The parameters sent with the request (in querystring or body).
        --> upsert [bool] : Whether to insert data if it isn't found
        <-- [bool] True if successful
    '''

    if not collection: raise API_Error('No collection was specified to update data for this route! Check your Route configuration', 500)

    mongo_fields = request_params.copy()
    _id = mongo_fields.pop('_id', None)
    if _id:
        return collection.update_one({'_id': ObjectId(_id)}, {'$set': mongo_fields}, upsert=upsert).acknowledged
    else:
        raise API_Error('No ID supplied', 400)


def delete_data(request_params: dict, collection:Collection, delete_all:bool=False) -> bool:
    ''' Delete data from the collection with the parameters sent in an HTTP request.
        --> request_params [dict] : The parameters sent with the request (in querystring or body).
        --> delete_all [bool] : True if all records matching the filter should be deleted
        <-- True if records were deleted
    '''

    if not collection: raise API_Error('No collection was specified to delete data for this route! Check your Route configuration', 500)

    mongo_fields = request_params.copy()
    func = collection.delete_many if delete_all else collection.delete_one
    if mongo_fields.get('_id'):
        return func({'_id': ObjectId(mongo_fields.pop('_id'))}).deleted_count > 0
    else:
        raise API_Error('No ID supplied', 400)
