# Interface class
from .setting import Setting

# Utilities
import os

class App_Settings(Setting):
    ''' Used to specify and validate application settings '''

    CONFIG_TYPE = 'app_settings'

    # App Config
    APP_ENV = os.environ.get('APP_ENV', 'development')
    APP_ENABLE_CORS = os.environ.get('APP_ENABLE_CORS', 'False').capitalize() == 'True'
    APP_HOST = os.environ.get('APP_HOST', '0.0.0.0')
    APP_PORT = int(os.environ.get('APP_PORT', '5000'))

    APP_API_CLIENT_HEADERS = {"User-Agent": "Mozilla/5.0"}

    APP_LOG_CONFIG = os.environ.get('APP_LOG_CONFIG', 'True').capitalize() == 'True'
    APP_DEBUG_MODE = True

    def __init__(self, app_env:str=None, app_enable_cors:bool=None, app_host:str=None, app_port:int=None, app_api_client_headers:dict=None, app_log_config:bool=None):

        if app_env: App_Settings.APP_ENV = app_env
        os.environ['FLASK_ENV'] = App_Settings.APP_ENV

        if app_enable_cors != None: App_Settings.APP_ENABLE_CORS = app_enable_cors
        if app_host: App_Settings.APP_HOST = app_host
        if app_port: App_Settings.APP_PORT = app_port
        if app_api_client_headers: App_Settings.APP_API_CLIENT_HEADERS = app_api_client_headers

        if app_log_config: App_Settings.APP_LOG_CONFIG = app_log_config
        
        App_Settings.APP_DEBUG_MODE = True if App_Settings.APP_ENV in ['dev', 'development', 'uat'] else False
        os.environ['FLASK_DEBUG'] = '1' if App_Settings.APP_DEBUG_MODE else '0'


    @staticmethod
    def get_log_data():
        ''' Returns a list of the settings to log to console '''

        return [
            'CORS enabled for application' if App_Settings.APP_ENABLE_CORS else 'CORS disabled for application. Set `APP_ENABLE_CORS` to True in environment to enable it',
            f'Default API client headers are {App_Settings.APP_API_CLIENT_HEADERS}'
        ]