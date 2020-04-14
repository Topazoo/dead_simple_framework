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