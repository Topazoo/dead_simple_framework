# 🙈 Dead Simple Web Framework 🙉

[![Python](https://img.shields.io/badge/Python-3.5.7+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-1.1.1-yellow.svg)](https://flask.palletsprojects.com/en/1.1.x/)
[![MongoDB/Pymongo](https://img.shields.io/badge/MongoDB-4.2-green.svg)](https://docs.mongodb.com/drivers/pymongo)
[![PyPi](https://img.shields.io/badge/View%20On-PyPi-orange.svg)](https://pypi.org/project/dead-simple-framework/)


## Overview:

A dead simple framework for web applications:

Backend:

- Python 3.7 [Flask]
- MongoDB
- Celery
- TODO: Kafka Hooks
- TODO: Redis Hooks
- TODO: RabbitMQ Hooks

## Installing:

```sh
$ pip install dead-simple-framework
```


## Configuration:

TODO

## Example Application (`demo.py`):
\* MongoDB must be running *
```sh
$ mongod
```


```sh
$ rabbitmq-server
$ celery -A demo worker -l info
```

```python
from dead_simple_framework import Application

sample_config = {
    'routes': {
        '/demo': {
            'name': 'demo',
            'methods': ['GET', 'POST', 'DELETE', 'PUT'],
            'template': None,
            'defaults': None,
            'logic': None,
            'collection': 'demo'
        },
        '/': {
            'name': 'index',
            'methods': ['GET'],
            'template': None,
            'defaults': None,
            'logic': lambda: str(Application.run_task('add', [5, 8], kwargs={}).get()),
        }
    },
    'tasks': {
        'add': {
            'logic': lambda x,y: x + y,
            'schedule': None,
            'timeframe': None
        }
    }
}

app = Application(sample_config)
if __name__ == '__main__':
    app.run()
```

- Starts a local server at http://0.0.0.0:5000/

- Serves CRUD operations for MongoDB collection `demo` at endpoint `/demo`.

- Runs and returns the result of an asynchronous Celery task at endpoint `/`
