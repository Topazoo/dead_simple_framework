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
        }
    },
    'tasks': {
        'add': {
            'logic': lambda x,y: x + y,
            'schedule': None,
            'timeframe': None
        }, 
        'subtract': {
            'logic': lambda x,y: x - y,
            'schedule': None,
            'timeframe': None
        } 
    }
}

app = Application(sample_config)
if __name__ == '__main__':
    app.run()