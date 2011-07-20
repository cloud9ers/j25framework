import unittest
from test.TestConfiguration import TestConfiguration
from test.fixtures.MongoDBFixture import MongoDBFixture
import j25
from test.fixtures.RemoteMemStoreFixture import RemoteMemStoreFixture
import pymongo

_mongo = None
_worker = None

def setUpModule(module):
    module._mongo = MongoDBFixture()
    module._mongo.setUp()
    module._memcached = RemoteMemStoreFixture()   
    module._memcached.setUp()
    
def tearDownModule(module):
    module._mongo.tearDown()
    module._memcached.tearDown()
    
class GlobalsTest(unittest.TestCase):
    def setUp(self):
        self.config = TestConfiguration.create_instance()
        j25.config = self.config     

    def tearDown(self):
        self.config = None
                
#    def testCache(self):        
#        cache = j25.cache
#        self.assertNotEquals(None, cache)
##        self.assertTrue(isinstance(cache, CacheManager))
#        self.assertTrue(cache is j25.cache)
#        cacheObj = cache.get_cache_region('test', "mongodbCache")
#        cacheObj.set_value("Test", 55)
#        conn = pymongo.Connection("localhost",27017)
#        self.assertTrue('c9CachingDB' in conn.database_names())
#        db = conn.c9CachingDB
#        self.assertTrue('c9CachingCollection' in db.collection_names())
#        self.assertTrue(db.c9CachingCollection.count(), 1)
#        cacheRecord = db.c9CachingCollection.find_one()
#        self.assertEqual(55, cacheObj.get_value("Test"))  
#        self.assertTrue(cacheRecord["_id"], 'test')
#        self.assertTrue('Test' in cacheRecord["data"])
#        
#        # test when regions not defined
#        self.config.cache.regions = None
#        cache = j25.cache
#        self.assertNotEquals(None, cache)
##        self.assertTrue(isinstance(cache, CacheManager))
#        self.assertTrue(cache is j25.cache)       
#        cacheObj = cache.get_cache('test', expire=1000)
#        cacheObj.set_value("TestKey", 1000)
#        self.assertTrue(cacheObj.get("TestKey"), 1000)   
                

    def testMemCache(self):        
        cache = j25.cache
        self.assertNotEquals(None, cache)
#        self.assertTrue(isinstance(cache, CacheManager))
        self.assertTrue(cache is j25.cache)
        cacheObj = cache.get_cache_region('test', "memcached")
        cacheObj.set_value("Test", 55)
        self.assertEqual(55, cacheObj.get_value("Test"))  
        
        # test when regions not defined
        self.config.cache.regions = None
        cache = j25.cache
        self.assertNotEquals(None, cache)
#        self.assertTrue(isinstance(cache, CacheManager))
        self.assertTrue(cache is j25.cache)       
        cacheObj = cache.get_cache('test', expire=1000)
        cacheObj.set_value("TestKey", 1000)
        self.assertTrue(cacheObj.get("TestKey"), 1000)   
