# Dead Simple Web Framework

## Overview:

A dead simple framework for web applications:

Backend:

- Python 3.7 [Flask]
- MongoDB
- TODO: Kafka Hooks
- TODO: Redis Hooks
- TODO: RabbitMQ Hooks
- TODO: Celery Hooks

## Installing:

TODO


## Configuration:

TODO

## Example Application:
Starts a local server at http://0.0.0.0:5000/

Serves CRUD operations for MongoDB collection `demo` at endpoint `/demo`.

```python
from dead_simple_framework import Application

sample_config = {
    '/demo': {
        'name': 'demo',
        'methods': ['GET', 'POST', 'DELETE', 'PUT'],
        'template': None,
        'defaults': None,
        'logic': None,
        'collection': 'demo'
    }
}

Application(sample_config).run()
```
