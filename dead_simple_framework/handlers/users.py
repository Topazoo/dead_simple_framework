''' Builtin handler with default user routes '''

# Base class
from dead_simple_framework.api.main import RouteHandler
from .permissions import DefaultPermissionsRouteHandler, Permissions
from .login import LoginRouteHandler

# Password hashing
from passlib.hash import pbkdf2_sha256 as sha256

# JWT
from flask_jwt_extended import get_jwt_identity, set_access_cookies, set_refresh_cookies, unset_jwt_cookies

# Database
from ..database import Database, Indices, Index

# Responses
from ..api.utils import JsonError, JsonException, JsonResponse, delete_data, insert_data

# Flask HTTP
from flask import Request, Response

# Utils
from datetime import datetime, timedelta

# Typing
from pymongo.collection import Collection
from pymongo.errors import OperationFailure

# Settings
from ..config.settings import JWT_Settings


class UserRouteHandler(DefaultPermissionsRouteHandler):

    DEFAULT_PERMISSIONS = ['USER'] # TODO - Make dynamic
    VERIFIER_FAILED_MESSAGE = 'User not authorized'

    def __init__(self, permissions=Permissions(PUT='USER', PATCH='USER', GET='USER', DELETE='USER'), verifier=None):
        Indices.add_indices('users',[
            Index('username', -1, {'unique': True}),
            Index('email_address', -1, {'unique': True}),
        ], register=False)

        super().__init__(permissions, GET=self.GET, POST=self.POST, DELETE=self.DELETE, PUT=RouteHandler.PUT, verifier=verifier or self.verifier)


    @staticmethod
    def verifier(method, payload, identity):
        ''' Ensure users can only operate on their account '''

        if 'password' in payload: payload['password'] = sha256.hash(payload.get('password'))
        if method != 'POST' and JWT_Settings.APP_USE_JWT:
            if identity and 'ADMIN' in identity.get('permissions', []): 
                return True

            _id = payload.get('_id')
            if 'filter' in payload and not _id:
                _id = payload['filter'].get('_id')

            if not identity or not _id:
                return False

            if identity['_id'] != _id:
                return False

            permissions = payload.get('permissions')
            if 'filter' in payload and not permissions:
                permissions = payload['filter'].get('permissions')

            if permissions and not 'ADMIN' in identity.get('permissions', []):
                return False

        return True


    @classmethod
    def POST(cls, request:Request, payload, collection:Collection) -> Response:
        ''' Create a new user with a hashed password '''

        try:
            payload['password'] = sha256.hash(payload.get('password'))
            payload['permissions'] = cls.DEFAULT_PERMISSIONS
            _id = insert_data(payload, collection)
            
            identity = {'username': payload.get('username'), '_id': str(_id), 'permissions': payload['permissions']}
            access_token, refresh_token = LoginRouteHandler.update_stored_token(identity)

            response = JsonResponse({
                '_id': _id,
                'permissions': payload['permissions'],
                'session_expires': datetime.now() + timedelta(seconds=int(JWT_Settings.APP_JWT_LIFESPAN))
            })

            set_access_cookies(response, access_token)
            set_refresh_cookies(response, refresh_token)

            return response

        except OperationFailure as e:
            if e.code == 11000:
                field = list(e.details['keyValue'].keys())[0]
                return JsonException('POST', f'{field} [{e.details["keyValue"][field]}] already exists', 409)
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
            if result:
                response = JsonResponse({'success': True})
                unset_jwt_cookies(response)
                return response

            return JsonError(f'User {identity["username"]} not found in database!', 404)

        except Exception as e:
            return JsonException('DELETE', e)
