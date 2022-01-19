# Typing
from typing import Dict
from bson import ObjectId

class Fixtures:
    ''' Class to facilitate applying database fixtures '''

    def __init__(self, fixtures:Dict[str, list]=None) -> None:
        self.fixtures = self._validate_fixtures(fixtures)
        
    def _validate_fixtures(self, fixtures:Dict[str, list]) -> Dict[str, list]:
        ''' Validate fixture structure and return fixtures'''

        if fixtures and not isinstance(fixtures, dict):
            raise ValueError(f'Error in fixture definitions. The fixture definition must be a dictionary')

        if fixtures:
            for collection, items in fixtures.items():
                if not isinstance(items, list):
                    raise ValueError(f'Error in fixture definitions for collection [{collection}]. The defined fixtures must be a list of dictionaries to insert in the database. Found a {type(items)}')

                for item in items:
                    if not isinstance(item, dict):
                        raise ValueError(f'Error in fixture definitions for collection [{collection}]. The fixture definition must be a list of dictionaries, the list contained type {type(item)}')
                    if not item.get('_id'):
                        raise ValueError(f'Error in fixture definitions for collection [{collection}]. The fixture definition:\n{item}\n is missing a MongoDB ObjectId in the _id field')
                    if not ObjectId.is_valid(item.get('_id')):
                        raise ValueError(f'Error in fixture definitions for collection [{collection}]. The fixture definition:\n{item}\n has an invalid MongoDB ObjectId in the _id field')
        
        if fixtures == None:
            return {}
        
        return fixtures
