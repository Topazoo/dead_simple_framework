# Utilities
from datetime import datetime
from json import JSONEncoder

class JSON_Encoder(JSONEncoder):
    ''' Custom JSON serializer '''

    def default(self, obj):
        try:                # Attempt regular serialization
            if isinstance(obj, datetime):
                return int(obj.timestamp() * 1000.0)
                
            return JSONEncoder.default(self, obj)
        except TypeError:   # Write as string on failure
            # TODO - [Logging] | Throw a warning when this occurs
            obj = str(obj)
            
            return obj