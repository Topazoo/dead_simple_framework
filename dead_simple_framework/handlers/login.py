''' Builtin handler with default login routes '''

# Base class
from .default import RouteHandler

# Password hashing
from passlib.hash import pbkdf2_sha256 as sha256

# JWT
from flask_jwt_extended import create_access_token, create_refresh_token

# Responses
from ..api.utils import JsonResponse, JsonError

# Flask HTTP
from flask import Request, Response

# Typing
from pymongo.collection import Collection


class LoginRouteHandler(RouteHandler):

    def __init__(self, schema:dict=None):
        super().__init__(POST=self.POST, DELETE=self.DELETE, schema=schema)


    @staticmethod
    def POST(request:Request, payload, collection:Collection) -> Response:
        ''' Attempt to log in for a specified user '''

        user = collection.find_one({'username': payload.get('username')})
        if not user:
            return JsonError(f"User [{payload.get('username')}] not found", 404)

        if not sha256.verify(payload.get('password'), user['password']):
            return JsonError("Incorrect Password", 400)

        permissions = user.get('permissions')
        if isinstance(permissions, str): permissions = [permissions]
        
        identity = {'user': user['username'], '_id': str(user['_id']), 'permissions': permissions}
        access_token = create_access_token(identity=identity)
        refresh_token = create_refresh_token(identity=identity)

        return JsonResponse({
            '_id': str(user['_id']),
            'access_token': access_token,
            'refresh_token': refresh_token
        })


    @staticmethod
    def DELETE(request:Request, payload, collection:Collection) -> Response:
        ''' Attempt to log out for a specified user '''

        # TODO - Implement
        return JsonResponse({'success': True})
