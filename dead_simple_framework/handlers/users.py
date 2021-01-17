''' Builtin handler with default user routes '''

# Base class
from .permissions import DefaultPermissionsRouteHandler

# Password hashing
from passlib.hash import pbkdf2_sha256 as sha256

# JWT
from flask_jwt_extended import create_access_token, create_refresh_token

# Responses
from ..api.utils import JsonError, JsonResponse, JsonException, delete_data, fetch_and_filter_data, insert_data, update_data

# Flask HTTP
from flask import Request, Response

# Typing
from pymongo.collection import Collection

from ..config.settings import App_Settings


class UserRouteHandler(DefaultPermissionsRouteHandler):

    USER_PERMISSIONS = ['USER'] # TODO - Make dynamic
    VERIFIER_FAILED_MESSAGE = 'User not authorized to access the data of other users'

    def __init__(self, permissions, verifier=None, schema:dict=None):
        super().__init__(permissions, GET=self.GET, POST=self.POST, PUT=self.PUT, DELETE=self.DELETE, verifier=verifier, schema=schema)


    @staticmethod
    def verifier(method, payload, identity):
        ''' Ensure users can only operate on their account '''

        if method != 'POST' and App_Settings.APP_USE_JWT:
            if identity and 'ADMIN' in identity.get('permissions', []): 
                return True # TODO - Dynamic admin

            _id = payload.get('_id')
            if 'filter' in payload and not _id:
                _id = payload['filter'].get('_id')

            if not identity or not _id:
                return False

            if identity['_id'] != _id:
                return False

        return True


    @classmethod
    def POST(cls, request:Request, payload, collection:Collection) -> Response:
        ''' Create a new user with a hashed password '''

        payload['password'] = sha256.hash(payload.get('password'))
        try:
            payload['permissions'] = cls.USER_PERMISSIONS
            _id = insert_data(payload, collection)
            
            identity = {'user': payload.get('username'), '_id': str(_id), 'permissions': payload['permissions']}
            access_token = create_access_token(identity=identity)
            refresh_token = create_refresh_token(identity=identity)

            return {
                'id': _id,
                'access_token': access_token,
                'refresh_token': refresh_token
            }

        except Exception as e:
            return JsonException('POST', e)


    @classmethod
    def PUT(cls, request:Request, payload, collection:Collection) -> Response:
        ''' Update a user ensuring hashed password '''

        if 'password' in payload: payload['password'] = sha256.hash(payload.get('password'))
        
        return {'success': update_data(payload, collection)}


    @classmethod
    def DELETE(cls, request:Request, payload, collection:Collection) -> Response:
        ''' Delete a user '''
        
        return {'success': delete_data(payload, collection)}


    @classmethod
    def GET(cls, request:Request, payload, collection:Collection) -> Response:
        ''' Get a user or users '''
        
        return {'data': fetch_and_filter_data(payload, collection)} # TODO - Dynamic redact
