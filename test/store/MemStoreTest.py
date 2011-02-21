import time
#from cloudmanager.stores.TCStore import TCStore
from j25.stores.LocalMemStore import LocalMemStore
from j25.stores.RemoteMemStore import RemoteMemStore
from test.fixtures.RemoteMemStoreFixture import RemoteMemStoreFixture
from test.fixtures.AppServerFixture import AppServerFixture

COLLECTION_ONE = 'collection_1'
COLLECTION_TWO = 'collection_2'
COLLECTION_THREE = 'collection_3'
COLLECTION_FOUR = 'collection_1'
COLLECTION_FIVE = 'collection_2'

PREFIX = 'prefix'
    
KEY_ONE = 'KEY1'
KEY_TWO = 'key2'
KEY_THREE = 'key3'
KEY_FOUR = 'key4'
KEY_FIVE = 'key5'
KEY_SIX = '%s_key6' % PREFIX
KEY_SEVEN = '%s_key7' % PREFIX
    
VALUE_ONE = 'value1'
VALUE_TWO = {'k1':1, 'k2':2}
VALUE_THREE = [1, 2, 3, 4]
VALUE_FOUR = 345555
VALUE_FIVE = 'v5'
VALUE_SIX = 'v6' 
VALUE_SEVEN = 'v7'



#import uuid
import unittest
#import os

#class TestTCStore(unittest.TestCase):
#    def setUp(self):
#        randomName = uuid.uuid4().hex + ".tc"
#        self._db = TCStore('/tmp/%s' % randomName, TCStore.BTREE)
#        
#    def tearDown(self):
#        self._db.close()
#        os.system("rm -rf /tmp/*.tc")
#    
#    def testBasicPutGet(self):
#        _testBasicPutGet(self)
#    
#    def testKeys(self):
#        _testKeys(self)

def setUpModule(module):
    pass
    
def tearDownModule(module):
    pass

class MemStoreTest(unittest.TestCase):
    def setUp(self):           
        self._db = LocalMemStore(COLLECTION_ONE)
        
    def tearDown(self):
        self._db.close()
    
    def testBasicPutGet(self):
        _testBasicPutGet(self)
    
    def testKeys(self):
        _testKeys(self)


class RemoteMemStoreTest(unittest.TestCase):
    
    def setUp(self):
        self._memCached = RemoteMemStoreFixture()
        self._memCached.setUp()
        self.appServerFixture = AppServerFixture()
                
        #Start server
        self.appServerFixture.setUp()
  
        self._db = RemoteMemStore(self.appServerFixture.config, COLLECTION_ONE )
            
    def testPutGet(self):
        self.assertRaises(KeyError, self._db.get, KEY_THREE)
        self.assertTrue(self._db.put(KEY_THREE, VALUE_THREE))
        self.assertEquals(self._db.get(KEY_THREE), VALUE_THREE) 
        self.assertNotEquals(self._db.get(KEY_THREE), VALUE_FOUR)
        self.assertRaises(KeyError, self._db.put, KEY_THREE, VALUE_THREE)
        
    def testDelete(self):
        self.assertTrue(self._db.delete, KEY_FOUR)
        self.assertTrue(self._db.put(KEY_FOUR, VALUE_FOUR))
        self.assertTrue(self._db.put(KEY_FIVE, VALUE_FIVE))      
        self._db.delete(KEY_FOUR)
        self.assertTrue(self._db.put(KEY_FOUR, VALUE_FOUR))
        self.assertRaises(KeyError, self._db.put, KEY_FOUR, VALUE_FOUR)
            
    def tearDown(self):
        self._db = None
        self._memCached.tearDown()
        self.appServerFixture.tearDown() 
    
def _testBasicPutGet(test):
    test._db.put("Ahmed", "Soliman")
    test.assertEquals(test._db.keys(), ['Ahmed'])
    test.assertEquals(test._db.get('Ahmed'), 'Soliman')
    test.assertRaises(KeyError, test._db.put, "Ahmed", "Teet")
    test.assertEquals(test._db.keys(), ['Ahmed'])
    test.assertNotEquals(test._db.get('Ahmed'), 'Teet')
    try:
        test._db.get("Nothing")
        test.fail("Should have thrown a KeyError Exception here")
    except KeyError, _:
        pass
    except:
        test.fail("Should have thrown a KeyError Exception here")
        raise
    
def _testKeys(test):
    for i in range(1, 100):
        test._db.put("Key%s" % i, "Value%s" % i)
    test.assertEquals(len(test._db.keys()), 99)
    keysOriginal = test._db.keys()
    keysOnTheFly = ['Key%s' % j for j in range(1, 100)]
    if keysOriginal == keysOnTheFly:
        test.fail("Keys are not matched %s != %s" % (keysOnTheFly, keysOnTheFly))
    
    keysOriginal = test._db.keys(max=20)
    keysOnTheFly = ['Key%s' % k for k in range(1, 21)]
    
    if keysOriginal == keysOnTheFly:
        test.fail("Keys are not matched %s != %s" % (keysOnTheFly, keysOnTheFly))
    
    for i in range(1, 30):
        test._db.put('Test%s' % i, 'TestValue%s' % i)
    test.assertEquals(len(test._db.keys('Tes')), 29)

    keysOriginal = test._db.keys('Test')
    keysOnTheFly = ['Test%s' % k for k in range(1, 29)]

    if keysOriginal == keysOnTheFly:
        test.fail("Keys are not matched %s != %s" % (keysOnTheFly, keysOnTheFly))
