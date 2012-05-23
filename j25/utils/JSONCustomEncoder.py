from simplejson.encoder import JSONEncoder
from datetime import datetime, date, time
from bson.objectid import ObjectId
from mongoengine.document import Document
from mongoengine.queryset import QuerySet

class JSONCustomEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, QuerySet):
            return list(obj)
        if isinstance(obj, Document):
            doc = obj.to_mongo()
            try:
                doc.pop('_cls')
                doc.pop('_types')
            except:
                pass
            return doc
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat().replace('T', ' ')
        elif isinstance(obj, (date, time)):
            return obj.isoformat()
        return JSONEncoder.default(self, obj)
        
