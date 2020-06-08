# Flask
from flask import Blueprint, render_template

# Internal API 
from .api import API

# Encoding
import json

# Debug
from pprint import pprint

# TODO - [Useability]     | RouteConfig class to allow a route to be created with hinting/linting enabled
# TODO - [Extendability] | Allow `logic` as default and method specific logic

class Router:
    ''' Module allowing route specification as a list of dictionaries in config/routes.py'''

    @staticmethod
    def register_routes(app, routes:dict):   
        ''' Register all routes in config/routes.py '''

        API.ROUTES = routes     # Copy routes to the internal API cass it can reference them 
        for route in routes:
            # TODO - [Stability] | Check required structure for a route and throw specific validation errors

            # Create a Flask blueprint based on the config for this route in the `routes` dictionary
            blueprint = Blueprint(routes[route]['name'], __name__)
            # Then attach logic and URL, and other options specified in the config to the blueprint
            Router.configure_blueprint(route, routes[route]['name'], routes[route], blueprint)
            # Register the blueprint with the Flask app so HTTP requests can be directed to it's URL
            app.register_blueprint(blueprint)


    @staticmethod
    def configure_blueprint(route_path:str, route_name: str, route_dict: dict, blueprint: Blueprint):
        ''' Adds configurations to the route Blueprint based on the dictionary specification '''

        # Set the logic that should fire when this URL is hit
        view_func = API.main if route_dict.get('collection') else route_dict['logic']

        # Set the blueprint to the URL specified in the route configuration
        blueprint.add_url_rule(route_path, route_name, view_func=view_func, methods=route_dict['methods'], **({'defaults': route_dict['defaults']} if route_dict.get('defaults') else {}))
