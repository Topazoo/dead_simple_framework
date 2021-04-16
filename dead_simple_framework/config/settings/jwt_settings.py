# Interface class
from .setting import Setting

# Utilities
import os, json

class JWT_Settings(Setting):
    ''' Used to specify and validate JSON web token settings '''

    CONFIG_TYPE = 'jwt_settings'

    # JWT Config
    APP_USE_JWT = os.environ.get('APP_USE_JWT', 'False').capitalize() == 'True'
    APP_CSRF_PROTECT = os.environ.get('APP_CSRF_PROTECT', 'False').capitalize() == 'True'
    APP_JWT_KEY = os.environ.get('APP_JWT_KEY', 'default')
    APP_JWT_LIFESPAN = os.environ.get('APP_JWT_LIFESPAN', 600)
    APP_PERMISSIONS = json.loads(os.environ.get('APP_PERMISSIONS', '["ADMIN", "USER"]'))

    def __init__(self, app_use_jwt:bool=None, app_csrf_protect:bool=None, app_jwt_key:str=None, app_jwt_lifespan:int=None, app_permissions:list=None):

        if app_use_jwt: JWT_Settings.APP_USE_JWT = app_use_jwt
        if app_csrf_protect: JWT_Settings.APP_CSRF_PROTECT = app_csrf_protect
        if app_jwt_key: JWT_Settings.APP_JWT_KEY = app_jwt_key
        if app_jwt_lifespan: JWT_Settings.APP_JWT_LIFESPAN = app_jwt_lifespan

        if app_permissions: JWT_Settings.APP_PERMISSIONS = list(set(app_permissions + ['ADMIN']))

    @staticmethod
    def get_log_data():
        ''' Returns a list of the settings to log to console '''

        return [
            f'JSON Web Token verfication is {"enabled" if JWT_Settings.APP_USE_JWT else "disabled. Set `APP_USE_JWT` to True in environment to enable it"}',
            f'The current JWT key is {"*unsafe* and should be changed" if JWT_Settings.APP_JWT_KEY == "default" else "safe"}. The current token lifespan is {JWT_Settings.APP_JWT_LIFESPAN} seconds' if JWT_Settings.APP_USE_JWT else '',
            f'CSRF protection is currently {"enabled" if JWT_Settings.APP_CSRF_PROTECT else "disabled. Set `APP_CSRF_PROTECT` to True in environment to enable it"}',
        ]
