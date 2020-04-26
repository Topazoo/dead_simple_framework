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
            'logic': lambda: str(Task_Manager.run_task('add', [5, 8], kwargs={}).get()),
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
            'timeframe': None
        },
        'insert': {
            'logic': lambda: Database(collection='insert').connect().insert_one({'test': 'doc'}),
            'schedule': {}, # Default - every minute
            'timeframe': None
        }
    }
}

app = Application(sample_config)
if __name__ == '__main__':
    app.run()