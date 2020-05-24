# Base Encoder
from flask.json import JSONEncoder

# Utilities
import json

class JSON_Encoder(JSONEncoder):
    ''' Custom JSON serializer '''

    def default(self, obj):
        try:                # Attempt regular serialization
            obj = JSONEncoder.default(self, obj)
        except TypeError:   # Write as string on failure
            obj = str(obj)
            
            return obj