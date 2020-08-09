# Flask
from flask import Flask 
from flask_cors import CORS

# Routing
from .router import Router

#Encoding
from .encoder import JSON_Encoder

# Async Tasks
from .tasks import Task_Manager

# App-wide settings
from .config.settings.main import Settings

# Utilities
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

        # Create Flask application
        self.app = Flask(__name__)

        # Log 3rd party configuration
        Settings.log_config()

        # Register a custom encoder for JSON serialization
        # [Note] - This currently just bypasses errors by casting the offending data to a string :)
        self.app.json_encoder = JSON_Encoder

        # Register all HTTP routes that should be available based on the application config
        Router.register_routes(self.app, config['routes'])
        
        # Initialize inherited asynchronous task management ability
        super().__init__(dynamic_tasks=config.get('tasks'))

        if Settings.APP_ENABLE_CORS: CORS(self.app)

        Application._app = self


    def run(self):
        ''' Runs the server '''

        #self.app.run(host=os.environ.get('FLASK_RUN_HOST', '0.0.0.0'), debug=(os.environ.get('APP_DEBUG') == 'True'))
        self.app.run(
            host=Settings.APP_HOST, 
            debug=Settings.APP_DEBUG_MODE
        )
