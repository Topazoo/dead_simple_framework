# 🙈 Dead Simple Web Framework 🙉

[![Python](https://img.shields.io/badge/Python-3.5.7+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-1.1.1-yellow.svg)](https://flask.palletsprojects.com/en/1.1.x/)
[![MongoDB/Pymongo](https://img.shields.io/badge/MongoDB-4.2-green.svg)](https://docs.mongodb.com/drivers/pymongo)
[![PyPi](https://img.shields.io/badge/View%20On-PyPi-orange.svg)](https://pypi.org/project/dead-simple-framework/)


## Overview:

A RESTful Flask framework with MongoDB, Redis, Celery, Slack and Sentry integrations:

Backend:

- Flask [Framework]
- MongoDB [Database]
- Redis [Cache]
- Celery + RabbitMQ [Async Tasks]
- Slack + Sentry [Logging]

## Installing:

```sh
$ pip install dead-simple-framework
```


## Configuration:

TODO - DOCS

## Example Application (`demo.py`):


```python
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
```

- Starts a local server at http://0.0.0.0:5000/

- Serves CRUD operations for MongoDB users collection `users` at endpoint `/api/users`

- Issues JWT tokents for created users at endpoint `/api/authenticate`

- Serves CRUD operations for MongoDB collection `posts` at endpoint `/api/posts`

- Demos errors at endpoint `/error`

