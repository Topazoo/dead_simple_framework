''' Builtin handler with default login routes '''

# Base class
from .default import RouteHandler

# Password hashing
from passlib.hash import pbkdf2_sha256 as sha256

# Database
from ..database import Database

# JWT
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_refresh_token_required, get_jwt_identity, decode_token
from ..jwt import jwt

# Utils
from ..api.utils import JsonError, update_data, delete_data
from datetime import datetime

# Flask HTTP
from flask import Request, Response

# Typing
from pymongo.collection import Collection
from typing import Tuple


class LoginRouteHandler(RouteHandler):

    def __init__(self, schema:dict=None):
        super().__init__(POST=self.POST, PUT=self.PUT, DELETE=self.DELETE, schema=schema)

        @jwt.token_in_blacklist_loader
        def check_if_token_revoked(decoded_token):
            return self.is_token_revoked(decoded_token)


    @staticmethod
    def is_token_revoked(token:dict):
        ''' Check if the token for a given user has been revoked '''

        with Database(collection='_jwt_tokens') as db:
            if not db.find_one({'token': token['jti']}):
                return True

        return False


    @staticmethod
    def update_stored_token(identity:dict) -> Tuple[str, str]:
        ''' Generate and update the stored access and refresh token for a user '''

        access_token = create_access_token(identity=identity)
        refresh_token = create_refresh_token(identity=identity)

        with Database(collection='_jwt_tokens') as collection:
            update_data({
                '_id': identity['_id'],
                'username': identity['username'],
                'token': decode_token(access_token)['jti'],
                'modified_on': datetime.now()
            }, collection, upsert=True)

        return access_token, refresh_token


    @classmethod
    def POST(cls, request:Request, payload, collection:Collection) -> Response:
        ''' Attempt to log in for a specified user '''

        user = collection.find_one({'username': payload.get('username')})
        if not user:
            return JsonError(f"User [{payload.get('username')}] not found", 404)

        if not sha256.verify(payload.get('password'), user['password']):
            return JsonError("Incorrect Password", 400)

        permissions = user.get('permissions')
        if isinstance(permissions, str): permissions = [permissions]
        
        identity = {'username': user['username'], '_id': str(user['_id']), 'permissions': permissions}
        access_token, refresh_token = cls.update_stored_token(identity)

        return {
            '_id': str(user['_id']),
            'access_token': access_token,
            'refresh_token': refresh_token
        }


    @classmethod
    @jwt_refresh_token_required
    def PUT(cls, request:Request, payload, collection:Collection) -> Response:
        ''' Create a refresh token '''

        identity = get_jwt_identity()
        if not identity:
            raise JsonError('Could not refresh access token, failed to validate refresh token')

        access_token, refresh_token = cls.update_stored_token(identity)
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }


    @staticmethod
    def DELETE(request:Request, payload, collection:Collection) -> Response:
        ''' Attempt to log out for a specified user '''

        identity = get_jwt_identity()
        if not identity:
            raise JsonError('Could not delete access token, failed to validate access token')

        with Database(collection='_jwt_tokens') as collection:
            result = delete_data({'_id': identity['_id']}, collection, delete_all=True)

        return {'success': result}
