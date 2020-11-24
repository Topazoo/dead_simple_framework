from dead_simple_framework import Application, Task_Manager, Database, API, Route, Task
from random import choice

WEBSITES =[
    "http://www.google.com",
    "http://www.yahoo.com",
    "http://www.ebay.com",
    "http://www.cnn.com",
    "http://www.pbs.org",
    "https://www.reddit.com/",
]

def get_websites(n):
    _websites = [*WEBSITES]
    res = []
    for x in range(n):
        res.append(choice(_websites))
        _websites.remove(res[-1])

    return res


sample_config = {
    'routes': {
        'insert': Route( # A route with automatic CRUD support
            url='/insert',
            methods=['GET', 'POST', 'DELETE', 'PUT'],
            collection='insert',
        ),
        'demo': { # Another route with automatic CRUD support
            'name': 'demo',
            'methods': ['GET', 'POST', 'DELETE', 'PUT'],
            'defaults': None,
            'logic': None,
            'collection': 'demo'
        },
        '/api/refresh': {  # Route that runs an async task (API call)
            'name': 'call',
            'methods': ['GET'],
            'defaults': None,
            'logic': lambda x,y: str(Task_Manager.run_task('scheduled_call')),
        },
        '/': {  # Route that fetches the last result of an async task (API call)
            'name': 'call_cached',
            'methods': ['GET'],
            'defaults': None,
            'logic': lambda x,y: str(Task_Manager.get_result('scheduled_call'))
        },
        '/add': {  # Route that fetches the last result of an async task (API call)
            'name': 'add',
            'methods': ['GET'],
            'defaults': None,
            'logic': lambda x,y: str(Task_Manager.run_task('add'))
        },
    },

    'tasks': { # Async tasks available to the Task_Manager [celery] to schedule or run
        'add': {        # Simple Addition Task (with default arguments) 
            'logic': lambda x,y: x + y,
            'schedule': None,
            'default_args': (2,2)
        },
        'insert': {     # Periodic Database Insert Task 
            'logic': lambda res: Database(collection='insert').connect().insert_one({'test': 'doc', 'result': res}),
            'schedule': {}, # Default - every minute
            'depends_on': 'add' # Return value substituted for `res`
        },
        'call_api': {   # API Call Task
            'logic': lambda url, params=None: str(API.get(url, params, ignore_errors=False, retry_ms=10000, num_retries=20).content),
        },
        'scheduled_call': Task( # Make 3 parallel API calls
            name='scheduled_call',
            logic=lambda: Task_Manager.parallelize([['call_api', [x]] for x in get_websites(3)]),
            schedule={}
        )
    }
}

app = Application(sample_config)
if __name__ == '__main__':
    app.run()