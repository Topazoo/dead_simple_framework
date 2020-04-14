# :see_no_evil: Dead Simple Web Framework :hear_no_evil:

[![Python](https://img.shields.io/badge/Python-3.5.7+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-1.1.1-yellow.svg)](https://flask.palletsprojects.com/en/1.1.x/)
[![MongoDB/Pymongo](https://img.shields.io/badge/MongoDB-4.2-green.svg)](https://docs.mongodb.com/drivers/pymongo)
[![PyPi](https://img.shields.io/badge/View%20On-PyPi-orange.svg)](https://pypi.org/project/dead-simple-framework/)


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

```sh
$ pip install dead-simple-framework
```


## Configuration:

TODO

## Example Application:
\* MongoDB must be running *
```sh
$ mongod
```

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

Starts a local server at http://0.0.0.0:5000/

Serves CRUD operations for MongoDB collection `demo` at endpoint `/demo`.
