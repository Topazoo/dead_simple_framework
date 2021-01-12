''' Builtin handler for routes with permissions '''

# Clients
import os

# Base class
from .default import DefaultRouteHandler, RouteHandler

# Helper method
from ..api import JsonResponse

# Settings
from ..config import App_Settings

# JWT
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

# Typing
from typing import Callable, Union


class Permissions:
    ''' Class that stores allowed permissions for each method '''

    DEFAULT_PERMISSIONS_LIST = os.environ.get('DEFAULT_PERMISSIONS_LIST', ['ADMIN', 'USER']) # TODO - Move to Config

    def __init__(self, GET:list=None, POST:list=None, DELETE:list=None, PUT:list=None, PATCH:list=None, OPTIONS:list=None):
        self.GET = GET
        self.POST = POST
        self.DELETE = DELETE
        self.PUT = PUT
        self.PATCH = PATCH
        self.OPTIONS = OPTIONS


class PermissionsRouteHandler(RouteHandler):
    ''' Route that only allows access for specific user permissions '''

    @staticmethod
    def hasPermission(current_user:dict, route_permissions:list) -> bool:
        ''' Checks if the current user has permission to access the resource '''

        if not current_user or not current_user.get('permissions'): return False
        if 'ADMIN' in current_user.get('permissions'): return True # TODO - Dynamic admin
        if any(role in route_permissions for role in current_user.get('permissions')):
            return True

        return False


    def permissionDecorator(self, method:Callable, permissions:Union[list,str]=None):
        if not method: return method

        if isinstance(permissions, str):
            permissions = [permissions]

        def accessIfPermission(request, payload, collection):
            if permissions and App_Settings.APP_USE_JWT:
                verify_jwt_in_request()
                current_user = get_jwt_identity() # TODO - Custom error handling
                payload['_JWT_Identity'] = current_user
                if not self.hasPermission(current_user, permissions):
                    return JsonResponse({'Error': f'User {current_user} does not have access to this resource'}, 403)
            return method(request, payload, collection)
        return accessIfPermission


    def __init__(self, permissions:Permissions, GET:Callable=None, POST:Callable=None, DELETE:Callable=None, PUT:Callable=None, PATCH:Callable=None, OPTIONS:Callable=None, schema:dict=None):
        self.permissions = permissions
        self.GET = self.permissionDecorator(GET, self.permissions.GET)
        self.POST = self.permissionDecorator(POST, self.permissions.POST)
        self.DELETE = self.permissionDecorator(DELETE, self.permissions.DELETE)
        self.PUT = self.permissionDecorator(PUT, self.permissions.PUT)
        self.PATCH = self.permissionDecorator(PATCH, self.permissions.PATCH)
        self.OPTIONS = self.permissionDecorator(OPTIONS, self.permissions.OPTIONS)

        self.methods = list(filter(lambda x: getattr(self,x) != None, self.SUPPORTED_HTTP_METHODS))


class DefaultPermissionsRouteHandler(PermissionsRouteHandler, DefaultRouteHandler):
    ''' Route that only allows access for specific user permissions '''

    def __init__(self, permissions:Permissions, GET:Callable=None, POST:Callable=None, DELETE:Callable=None, PUT:Callable=None, PATCH:Callable=None, OPTIONS:Callable=None, schema:dict=None):
        self.permissions = permissions

        self.GET = self.permissionDecorator(GET or self.GET, self.permissions.GET)
        self.POST = self.permissionDecorator(POST or self.POST, self.permissions.POST)
        self.DELETE = self.permissionDecorator(DELETE or self.DELETE, self.permissions.DELETE)
        self.PUT = self.permissionDecorator(PUT or self.PUT, self.permissions.PUT)
        self.PATCH = self.permissionDecorator(PATCH or PATCH, self.permissions.PATCH)
        self.OPTIONS = self.permissionDecorator(OPTIONS or OPTIONS, self.permissions.OPTIONS)

        self.methods = list(filter(lambda x: getattr(self,x) != None, self.SUPPORTED_HTTP_METHODS))
