# Flask
from flask import Blueprint

# Internal API 
from .handlers import RouteHandler, DefaultRouteHandler

# Route config class
from .config import Route

# Encoding
import json

# Typing
from typing import Union

# Debug
from pprint import pprint

# TODO - [Useability]     | RouteConfig class to allow a route to be created with hinting/linting enabled
# TODO - [Extendability] | Allow `logic` as default and method specific logic

class Router:
    ''' Module allowing route specification as a list of dictionaries in config/routes.py'''

    @staticmethod
    def _cast_route(url:str, route_config:Union[dict, Route]) -> Route:
        ''' Takes a route config dictionary and casts it to a `Route` object 
        
        Args:
            url (str): The url for this route
            route_config (Union[dict, Route]): The configuration for the route. Can be passed a config dictionary
                or an already created route. If the latter if passed, no conversion is necessary
        Returns:
            A `Route` object representing the config for that route
        '''
        
        return route_config if isinstance(route_config, Route) else Route.from_dict(url, route_config)


    @classmethod
    def register_routes(cls, app, routes:dict):   
        ''' Register all routes in config/routes.py '''
 
        route_objs ={}
        for route_url, route in routes.items():
            # Cast config to `Route` object if it's a dictionary
            route = cls._cast_route(route_url, route)
            # Create a Flask blueprint based on the config for this route in the `routes` dictionary
            blueprint = Blueprint(route.name, __name__)
            # Then attach logic and URL, and other options specified in the config to the blueprint
            cls.configure_blueprint(route, blueprint)
            # Register the blueprint with the Flask app so HTTP requests can be directed to it's URL
            app.register_blueprint(blueprint)
            # Add the Route object to the internal registry
            route_objs[route.url] = route

        RouteHandler.ROUTES = route_objs # Copy routes to RouteHandler instances

    @staticmethod
    def configure_blueprint(route:Route, blueprint: Blueprint):
        ''' Adds configurations to the route Blueprint based on the dictionary specification '''

        if not route.handler: # Default
            route.handler = DefaultRouteHandler()

        # Set the blueprint to the URL specified in the route configuration
        blueprint.add_url_rule(route.url, route.name, view_func=route.handler.main, methods=route.handler.methods, **({'defaults': route.defaults} if route.defaults else {}))
