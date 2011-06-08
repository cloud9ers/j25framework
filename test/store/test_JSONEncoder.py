import unittest
import simplejson
from j25.utils.JSONCustomEncoder import JSONCustomEncoder
from datetime import datetime, date, time
from bson.objectid import ObjectId

def setUpModule(module):
    pass
    
def tearDownModule(module):
    pass

class JSONCustomEncoderTest(unittest.TestCase):
    def testObjectIdEncoder(self):
        oid1 = ObjectId()
        oidJson1 = simplejson.dumps(oid1, cls=JSONCustomEncoder)
        self.assertEqual(str(oid1), eval(oidJson1))
        
    def testDateTimeEncoder(self):
        #testing datetime class
        doc1 = {}
        doc1['dateTime'] = datetime(2011, 1, 4, 14, 1, 10)
        docJson1 = simplejson.dumps(doc1, cls=JSONCustomEncoder)
        self.assertEqual('{"dateTime": "2011-01-04 14:01:10"}', docJson1)
        doc2 = {}
        doc2['dateTime'] = datetime(2011, 1, 4)
        docJson2 = simplejson.dumps(doc2, cls=JSONCustomEncoder)
        self.assertEqual('{"dateTime": "2011-01-04 00:00:00"}', docJson2)
        docList = [doc1, doc2]
        docJsonList = simplejson.dumps(docList, cls=JSONCustomEncoder)
        self.assertTrue(isinstance(docList, list))
        self.assertEqual('[{"dateTime": "2011-01-04 14:01:10"}, {"dateTime": "2011-01-04 00:00:00"}]', docJsonList)
        #testing date class        
        doc3 = {}
        doc3['dateTime'] = date(2011, 3, 23)
        docJson3 = simplejson.dumps(doc3, cls=JSONCustomEncoder)
        self.assertEqual('{"dateTime": "2011-03-23"}', docJson3)
        #testing time class        
        doc4 = {}
        doc4['dateTime'] = time(14, 05, 44)
        docJson4 = simplejson.dumps(doc4, cls=JSONCustomEncoder)
        self.assertEqual('{"dateTime": "14:05:44"}', docJson4)