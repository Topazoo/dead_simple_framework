''' Builtin handler with default JWT access and refresh token provisioning '''

# Base class
from .default import RouteHandler

# JWT
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_refresh_token_required, get_jwt_identity

# Responses
from ..api.utils import JsonResponse

# Flask HTTP
from flask import Request, Response

# Typing
from pymongo.collection import Collection


class TokenRouteHandler(RouteHandler):

    @staticmethod
    @jwt_refresh_token_required
    def PUT(request:Request, payload, collection:Collection) -> Response:
        ''' Create a refresh token '''

        current_user = get_jwt_identity()
        access_token = create_access_token(identity = current_user)
        refresh_token = create_refresh_token(identity = current_user)
        return JsonResponse({
            'access_token': access_token,
            'refresh_token': refresh_token
        })
