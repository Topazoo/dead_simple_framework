# Flask
from flask import Flask 
from flask_cors import CORS

# Routing
from .router import Router

#Encoding
from .encoder import JSON_Encoder

# Async Tasks
from .tasks import Task_Manager

# Database
from .database import Indices, Index

# App-wide settings
from .config.settings.main import Settings

# JWT
from .jwt import jwt

# Sentry
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Utils
import os

# Debug
import logging

# TODO - [Logging] | Configure application wide logging
# TODO - [Useability] | Use `Task_Manager` via adapter to hide unwanted methods/attributes 

class Application(Task_Manager):
    ''' Main application driver

        Takes a configuration dictionary that can specify:
          - HTTP routes             [URL, Allowed Methods, Custom Logic]
          - Asynchronous Tasks      [Schedule, Cacheable, Default Args/Kwargs]

        Runs a server based on that configuration
     '''

    _app = None     # Internal reference - Hacky way to allow classmethods to access a global state (probably a bad idea)

    def __init__(self, config:dict):
        ''' Initialize the server based on the configuration dictionary '''

        Settings(**config.get('settings', {})) 

        # Create database indices
        self.indices = Indices.from_dict(config.get('indices'))

        # Create Flask application
        self.app = Flask(__name__)

        # Add JWT support
        if Settings.APP_USE_JWT:
            self._setup_jwt()
            self.indices.add_indices('_jwt_tokens', [
                Index(field='modified_on', order=-1, properties={'expireAfterSeconds': int(Settings.APP_JWT_LIFESPAN or 600)}),
                Index(field='token', order=-1)
            ], False)

        # Add Sentry support
        self._setup_sentry()

        # Register database indices
        self.indices.register_indices()

        # Log 3rd party configuration
        Settings.log_config()

        # Register a custom encoder for JSON serialization
        # [Note] - This currently just bypasses errors by casting the offending data to a string :)
        self.app.json_encoder = JSON_Encoder

        # Register all HTTP routes that should be available based on the application config
        Router.register_routes(self.app, config['routes'])
        
        # Initialize inherited asynchronous task management ability
        super().__init__(dynamic_tasks=config.get('tasks'))

        # # TODO - Dynamic Resources
        if Settings.APP_ENABLE_CORS: CORS(self.app, resources=r'/api/*', supports_credentials=True)

        Application._app = self


    def _setup_jwt(self):
        ''' Adds JWT config options '''

        self.app.config['JWT_SECRET_KEY'] = Settings.APP_JWT_KEY
        self.app.config['JWT_BLACKLIST_ENABLED'] = True if Settings.APP_USE_JWT else False
        self.app.config['JWT_TOKEN_LOCATION'] = ['cookies']
        
        # TODO - Dynamic JWT Cookie setup
        self.app.config['JWT_COOKIE_SAMESITE'] = os.environ.get('JWT_COOKIE_SAMESITE', 'None')
        self.app.config['JWT_COOKIE_SECURE'] = os.environ.get('JWT_COOKIE_SECURE', 'false') == 'true'
        if Settings.APP_CSRF_PROTECT:
            self.app.config['JWT_COOKIE_CSRF_PROTECT'] = True
            self.app.config['JWT_CSRF_CHECK_FORM'] = True
        else:
            self.app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        
        jwt.init_app(self.app)


    def _setup_sentry(self):
        if Settings.USE_SENTRY and Settings.APP_SENTRY_HOST and Settings.APP_SENTRY_SLUG:
            sentry_sdk.init(f'https://{Settings.APP_SENTRY_HOST}.ingest.sentry.io/{Settings.APP_SENTRY_SLUG}', max_breadcrumbs=50, integrations=[FlaskIntegration()],)


    def run(self):
        ''' Runs the server '''

        self.app.run(host=Settings.APP_HOST, debug=Settings.APP_DEBUG_MODE, port=Settings.APP_PORT)
