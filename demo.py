from dead_simple_framework import Route, RouteHandler, Application
from dead_simple_framework.handlers import UserRouteHandler, LoginRouteHandler, Permissions, DefaultPermissionsRouteHandler
from dead_simple_framework.database import Indices
from dead_simple_framework.api.errors import API_Error
from dead_simple_framework.api.utils import JsonError

# Method that throws a sample error
def throw(msg): raise API_Error(msg, 400)

# App config for a simple blog application with user accounts
sample_config = {
    'routes': {
        # Users
        'users': Route(
            # Route with a built-in handler for creating, updating, fetching and deleting users
            # Only authenticated users can perform certain operations.
            # Adding a `verifier` to the class will let you allow only a specific user to update 
            # their data or delete their account.
            url = '/api/users',
            handler=UserRouteHandler(permissions=Permissions(
                PUT='USER', PATCH='USER', GET='USER', DELETE='USER'
            )),
            # The schema controls what data can be passed to the endpoint
            # In this case, a user ObjectId is required and the only property
            # supported. 
            schema={
                'GET': {
                    'type': 'object',
                    'properties': {
                        '_id': {'type': 'string'}
                    },
                    'required': ['_id']
                }
            },
            # The MongoDB collection where data for this route should be stored
            # It is passed to any overloaded method handlers (e.g. a custom GET method)
            collection='users'
        ),

        # Authentication
        'authentication': Route(
            # Route with a built-in handler for authenticating users and issuing a JSON Web Token
            url='/api/authenticate', 
            handler=LoginRouteHandler(),
            # It relies on the same collection as the core `users` route
            collection='users'
        ),

        # Posts
        'posts': Route(
            # Route with a builtin generic CRUD handler for creating, updating, fetching and deleting posts
            # Only authenticated users can perform certain operations.
            url='/api/posts',
            handler=DefaultPermissionsRouteHandler(permissions=Permissions(POST=['USER'], PUT=['USER'], PATCH=['USER'], DELETE=['USER'])),
            collection='posts'
        ),

        # Sample Error
        'error': Route(
            # Route that demonstrates built-in error handling
            url='/error',
            handler=RouteHandler(
                # Custom handlers allow a POST request or a GET request to create different errors
                POST=lambda request, payload: throw(f'POST - Error from payload {payload}'),
                GET=lambda request, payload: JsonError('This is a GET error', code=500),
            )
        ),
    },

    # Application settings
    'settings': {
        # JWT Settings determine if the app uses JWT, what the token lifespan will be and more
        'jwt_settings': {
            'app_use_jwt': True,
            'app_jwt_lifespan': 600,
            'app_permissions': ['USER', 'ADMIN'],
        }
    },

    # MongoDB indices for each collection used by the application
    'indices': Indices({
        'users': {
            'username': {
                'order': -1
            },
            'password': {
                'order': 1,
                'compound_with': 'username'
            }
        },
    })
}

if __name__ == '__main__':
    Application(sample_config).run()
