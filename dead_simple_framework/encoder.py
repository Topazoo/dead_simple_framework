from bson import ObjectId
from flask.json import JSONEncoder
import json

class JSON_Encoder(JSONEncoder):
    ''' Custom encoder for jsonify() '''

    def default(self, obj):
        try:
            obj = JSONEncoder.default(self, obj)
        except TypeError:
            obj = str(obj)
            
            return obj