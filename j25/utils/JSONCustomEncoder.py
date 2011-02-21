from simplejson.encoder import JSONEncoder
from datetime import datetime, date, time
from bson.objectid import ObjectId

class JSONCustomEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat().replace('T', ' ')
        elif isinstance(obj, (date, time)):
            return obj.isoformat()
        return JSONEncoder.default(self, obj)
        
