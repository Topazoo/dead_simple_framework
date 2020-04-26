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
- Celery + RabbitMQ
- TODO: Kafka Hooks
- TODO: Redis Hooks

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
from dead_simple_framework import Application, Task_Manager, Database

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
            'logic': lambda: str(Task_Manager.run_task('add', [5, 8], kwargs={})),
        },
        '/insert': {
            'name': 'insert',
            'methods': ['GET', 'POST', 'DELETE', 'PUT'],
            'template': None,
            'defaults': None,
            'logic': None,
            'collection': 'insert'
        }
    },
    'tasks': {
        'add': {
            'logic': lambda x,y: x + y,
            'schedule': None,
            'timeframe': None,
            'args': (2,2)
        },
        'insert': {
            'logic': lambda res: Database(collection='insert').connect().insert_one({'test': 'doc', 'result': res}),
            'schedule': {}, # Default - every minute
            'timeframe': None,
            'depends_on': 'add' # Return value substituted for `res`
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

- Runs an asynchronous chained value calculation and insert into the `insert` collection (viewable at `/insert`)
