# Interface class
from .setting import Setting

# Utilities
import os, json

class App_Settings(Setting):
    ''' Used to specify and validate application settings '''

    CONFIG_TYPE = 'app_settings'

    # App Config
    APP_ENV = os.environ.get('APP_ENV', 'development')
    APP_ENABLE_CORS = os.environ.get('APP_ENABLE_CORS', False)
    APP_HOST = os.environ.get('APP_HOST', '0.0.0.0')
    APP_PORT = int(os.environ.get('APP_PORT', '5000'))

    APP_API_CLIENT_HEADERS = {"User-Agent": "Mozilla/5.0"}

    APP_LOG_CONFIG = os.environ.get('APP_LOG_CONFIG', True)

    APP_USE_JWT = os.environ.get('APP_USE_JWT', False)
    APP_JWT_KEY = os.environ.get('APP_JWT_KEY', 'default')
    APP_JWT_LIFESPAN = os.environ.get('APP_JWT_LIFESPAN', 600)
    APP_PERMISSIONS = json.loads(os.environ.get('APP_PERMISSIONS', '["ADMIN", "USER"]'))

    APP_DEBUG_MODE = True

    def __init__(self, app_env:str=None, app_enable_cors:bool=None, app_host:str=None, app_port:int=None, 
                    app_api_client_headers:dict=None, app_log_config:bool=None, app_use_jwt:bool=None, 
                        app_jwt_key:str=None, app_jwt_lifespan:int=None, app_permissions:list=None):

        if app_env: App_Settings.APP_ENV = app_env
        os.environ['FLASK_ENV'] = App_Settings.APP_ENV

        if app_enable_cors != None: App_Settings.APP_ENABLE_CORS = app_enable_cors
        if app_host: App_Settings.APP_HOST = app_host
        if app_port: App_Settings.APP_PORT = app_port
        if app_api_client_headers: App_Settings.APP_API_CLIENT_HEADERS = app_api_client_headers

        if app_log_config: App_Settings.APP_LOG_CONFIG = app_log_config

        if app_use_jwt: App_Settings.APP_USE_JWT = app_use_jwt
        if app_jwt_key: App_Settings.APP_JWT_KEY = app_jwt_key
        if app_jwt_lifespan: App_Settings.APP_JWT_LIFESPAN = app_jwt_lifespan

        if app_permissions: App_Settings.APP_PERMISSIONS = list(set(app_permissions + ['ADMIN']))
        
        App_Settings.APP_DEBUG_MODE = True if App_Settings.APP_ENV in ['dev', 'development', 'uat'] else False
        os.environ['FLASK_DEBUG'] = '1' if App_Settings.APP_DEBUG_MODE else '0'


    @staticmethod
    def get_log_data():
        ''' Returns a list of the settings to log to console '''

        return [
            'CORS enabled for application' if App_Settings.APP_ENABLE_CORS else 'CORS disabled for application',
            f'JSON Web Token verfication is {"enabled" if App_Settings.APP_USE_JWT else "disabled"}.' +\
            f'The current key is {"*unsafe* and should be changed" if App_Settings.APP_JWT_KEY == "default" else "safe"}. The current token lifespan is {App_Settings.APP_JWT_LIFESPAN} seconds' if App_Settings.APP_USE_JWT else '',
            f'Default API client headers are {App_Settings.APP_API_CLIENT_HEADERS}'
        ]