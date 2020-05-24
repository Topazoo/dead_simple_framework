# Base Encoder
from flask.json import JSONEncoder

# Utilities
import json

class JSON_Encoder(JSONEncoder):
    ''' Custom encoder for jsonify() '''

    def default(self, obj):
        try:
            obj = JSONEncoder.default(self, obj)
        except TypeError:
            obj = str(obj)
            
            return obj