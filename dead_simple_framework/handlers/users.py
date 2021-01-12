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


class UserRouteHandler(DefaultPermissionsRouteHandler):

    USER_PERMISSIONS = ['USER'] # TODO - Make dynamic

    def __init__(self, permissions, schema:dict=None):
        super().__init__(permissions, GET=self.GET, POST=self.POST, PUT=self.PUT, DELETE=self.DELETE, schema=schema)


    @staticmethod
    def _valid_user_signature(payload):
        ''' Ensure users can only operate on their account '''

        if '_JWT_Identity' in payload and 'ADMIN' in payload['_JWT_Identity']['permissions']: 
            return True # TODO - Dynamic admin

        _id = payload.get('_id')
        if 'filter' in payload and not _id:
            _id = payload['filter'].get('_id')

        if '_JWT_Identity' not in payload or not _id:
            return False

        if payload['_JWT_Identity']['_id'] != _id:
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

            return JsonResponse({
                'id': _id,
                'access_token': access_token,
                'refresh_token': refresh_token
            })

        except Exception as e:
            return JsonException('POST', e)


    @classmethod
    def PUT(cls, request:Request, payload, collection:Collection) -> Response:
        ''' Update a user ensuring hashed password '''

        if 'password' in payload: payload['password'] = sha256.hash(payload.get('password'))
        try:
            if not cls._valid_user_signature(payload):
                return JsonError('User not authorized to update a different user', 403)
            return JsonResponse({'success': update_data(payload, collection)})
        except Exception as e:
            return JsonException('PUT', e)


    @classmethod
    def DELETE(cls, request:Request, payload, collection:Collection) -> Response:
        ''' Delete a user '''

        if 'password' in payload: payload['password'] = sha256.hash(payload.get('password'))
        try:
            if not cls._valid_user_signature(payload):
                return JsonError('User not authorized to delete a different user', 403)
            return JsonResponse({'success': delete_data(payload, collection)})
        except Exception as e:
            return JsonException('DELETE', e)


    @classmethod
    def GET(cls, request:Request, payload, collection:Collection) -> Response:
        ''' Get a user or users '''

        if 'password' in payload: payload['password'] = sha256.hash(payload.get('password'))
        try:
            if not cls._valid_user_signature(payload):
                return JsonError('User not authorized to view a different user', 403)
            return JsonResponse({'success': fetch_and_filter_data(payload, collection)}) # TODO - Dynamic redact
        except Exception as e:
            return JsonException('GET', e)
