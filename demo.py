from dead_simple_framework import Application, Task_Manager, Database, API
from random import randint
# A sample backend specified as a dictionary

sample_config = {
    'routes': { # HTTP Routes available 
        
        '/demo': { # Route with automatic CRUD support
            'name': 'demo',
            'methods': ['GET', 'POST', 'DELETE', 'PUT'],
            'template': None,
            'defaults': None,
            'logic': None,
            'collection': 'demo'
        },

        '/': {    # Route that runs an async task (addition)
            'name': 'index',
            'methods': ['GET'],
            'template': None,
            'defaults': None,
            'logic': lambda: str(Task_Manager.run_task('add')),
        },

        '/insert': { # Another route with automatic CRUD support
            'name': 'insert',
            'methods': ['GET', 'POST', 'DELETE', 'PUT'],
            'template': None,
            'defaults': None,
            'logic': None,
            'collection': 'insert'
        },

        '/call': {  # Route that runs an async task (API call)
            'name': 'call',
            'methods': ['GET'],
            'template': None,
            'defaults': None,
            'logic': lambda: str(Task_Manager.schedule_task('call_api', ['http://services.runescape.com/m=itemdb_oldschool/api/catalogue/detail.json', {'item': 56}])),
        },

        '/last': {  # Route that fetches a cached result from a scheduled task
            'name': 'last_add',
            'methods': ['GET'],
            'template': None,
            'defaults': None,
            'logic': lambda: str(Task_Manager.get_result('rand_add'))
        },
    },


    'tasks': { # Async tasks available to the Task_Manager [celery] to schedule or run
        
        'add': {        # Simple Addition Task (with default arguments) 
            'logic': lambda x,y: x + y,
            'schedule': None,
            'args': (2,2)
        },

        'insert': {     # Periodic Database Insert Task 
            'logic': lambda res: Database(collection='insert').connect().insert_one({'test': 'doc', 'result': res}),
            'schedule': {}, # Default - every minute
            'depends_on': 'add', # Return value substituted for `res`,
            'cache': False # Disable caching
        },

        'call_api': {   # API Call Task
            'logic': lambda url, params=None: API.get_json(url, params),
        },

        'rand_add': {   # Simple Addition Task (with random arguments) 
            'logic': lambda: randint(0, 1000) + randint(1, 10000),
            'schedule': {},  # Default - every minute,
            'cache': False
        },
    }
}

# Required boilerplate to run the app or the scheduler [RabbitMQ must be running]

# Command line:
# Celery | celery -A <path.to.app> worker -l info
# App    | python3 <app.py>

app = Application(sample_config)
if __name__ == '__main__':
    app.run()
