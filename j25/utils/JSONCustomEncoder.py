from simplejson.encoder import JSONEncoder
from datetime import datetime, date, time
from bson.objectid import ObjectId
from bson.dbref import DBRef
from mongoengine.document import Document, EmbeddedDocument
from mongoengine.queryset import QuerySet
from mongoengine.connection import get_db

class JSONCustomEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, QuerySet):
            return list(obj)
        if isinstance(obj, DBRef):
            doc = get_db().dereference(obj)
            try:
                doc.pop('_cls')
                doc.pop('_types')
            except:
                pass
            return doc
        if isinstance(obj, (Document, EmbeddedDocument)):
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
        
