''' Builtin handler with default user routes '''

# Base class
from dead_simple_framework.api.main import RouteHandler
from .permissions import DefaultPermissionsRouteHandler
from .login import LoginRouteHandler

# Password hashing
from passlib.hash import pbkdf2_sha256 as sha256

# JWT
from flask_jwt_extended import get_jwt_identity

# Database
from ..database import Database

# Responses
from ..api.utils import JsonException, delete_data, insert_data

# Flask HTTP
from flask import Request, Response

# Typing
from pymongo.collection import Collection
from pymongo.errors import OperationFailure

# Settings
from ..config.settings import App_Settings


class UserRouteHandler(DefaultPermissionsRouteHandler, LoginRouteHandler):

    DEFAULT_PERMISSIONS = ['USER'] # TODO - Make dynamic
    VERIFIER_FAILED_MESSAGE = 'User not authorized'

    def __init__(self, permissions, verifier=None, schema:dict=None):
        super(DefaultPermissionsRouteHandler, self).__init__(permissions, GET=self.GET, POST=self.POST, DELETE=self.DELETE, PUT=RouteHandler.PUT, verifier=verifier, schema=schema)
        Database.register_indices({'users': [{'indices': [('username', -1)], 'unique':True}]})

    @staticmethod
    def verifier(method, payload, identity):
        ''' Ensure users can only operate on their account '''

        if 'password' in payload: payload['password'] = sha256.hash(payload.get('password'))
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

        try:
            payload['permissions'] = cls.DEFAULT_PERMISSIONS
            _id = insert_data(payload, collection)
            
            identity = {'username': payload.get('username'), '_id': str(_id), 'permissions': payload['permissions']}
            access_token, refresh_token = cls.update_stored_token(identity)

            return {
                'id': _id,
                'access_token': access_token,
                'refresh_token': refresh_token
            }

        except OperationFailure as e:
            if e.code == 11000:
                return JsonException('POST', f'User [{e.details["keyValue"]["username"]}] already exists')
            else:
                raise e
        except Exception as e:
            return JsonException('POST', e)


    @classmethod
    def DELETE(cls, request:Request, payload, collection:Collection) -> Response:
        ''' Create a new user with a hashed password '''

        try:
            identity = get_jwt_identity()
            with Database(collection='_jwt_tokens') as tokens_collection:
                delete_data({'_id': payload['_id']}, tokens_collection, delete_all=True)
            
            result = delete_data(payload, collection)
            return {'success': result}

        except Exception as e:
            return JsonException('DELETE', e)
