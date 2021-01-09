from dead_simple_framework import Application, Task_Manager, Database, API, Route, RouteHandler, DefaultRouteHandler, Task
from random import choice

sample_config = {
    'routes': {
        'insert': Route( # A route with automatic CRUD support
            url='/insert',
            handler=DefaultRouteHandler(),
            collection='insert',
        ),
        'demo': Route( # Another route with automatic CRUD support (with all options specified)
            url='/demo',                    # The URL at which the server should handle requests
            defaults=None,                  # Default parameters to pass to the handler function for this URL
            database='db',                  # The database that should be passed to the handler function for this URL 
            collection='demo',              # The collection that should be passed to the handler function for this URL 
            handler=DefaultRouteHandler()   # A class specifying the handler functions to use based on the method used to access the URL 
        ),
        'refresh': Route(  # Route with a handler for the GET method that runs an async task (in this case an API call)
            url='/api/refresh',
            handler=RouteHandler(
                GET=lambda request, payload: str(Task_Manager.run_task('scheduled_call'))
            )
        ),
        'index': Route(  # Route that fetches the cached latest result of an async task (in this case an API call)
            url='/',
            handler=RouteHandler(
                GET=lambda request, payload: str(Task_Manager.get_result('scheduled_call'))
            )
        ),
        'add': Route(  # Route that runs an async task (in this case simple addition) and fetches the result
            url='/add',
            handler=RouteHandler(
                GET=lambda request, payload: str(Task_Manager.run_task('add'))
            )
        ),
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


app = Application(sample_config)
if __name__ == '__main__':
    app.run()