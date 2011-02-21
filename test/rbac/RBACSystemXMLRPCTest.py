#import unittest
#from test.fixtures.MongoDBFixture import MongoDBFixture
#from test.fixtures.RemoteMemStoreFixture import RemoteMemStoreFixture
#from framework.stores.StoreFactory import MongoStoreFactory
#from model.rbac.ResourcePermission import ResourcePermission
#from framework.ModelLoader import AutoModelLoader 
#from services.RBACSystemXMLRPC import RBACSystemXMLRPC
#from framework import Context
#from test.TestConfiguration import TestConfiguration
#from framework.CacheManagerImpl import CacheFactory
#
#_mongo = None
#_memCached = None
#
#def setUpModule(module):
#    module._mongo = MongoDBFixture()
#    module._mongo.setUp()   
#       
#def tearDownModule(module):
#    module._mongo.tearDown()    
#    
#class RBACSystemXMLRPCTest(unittest.TestCase):
#    def setUp(self):
#        import model
#        AutoModelLoader(model)
#        self._config = TestConfiguration.createInstance()
#        self._store = MongoStoreFactory.createInstance(self._config)
#        self._cache = CacheFactory.createInstance(self._config)
#        self._context = Context.ContextFactory.createContext(self._config, None)
#        self._memCached = RemoteMemStoreFixture()
#        self._memCached.setUp()  
#        
#    def tearDown(self):
#        self._memCached.tearDown()
#        self._store = None
#        self._cache = None
#        self._context = None
#        self._config = None
#        
#    def testRolesToCache(self):
#        ResourcePermission('p1', 'r1').save(self._store)
#        ResourcePermission('p2', 'r2').save(self._store)
#        ResourcePermission('p3', 'r3').save(self._store)
#        rp1 = ResourcePermission.findOne(self._store, ResourcePermission('p1', 'r1'))
#        rp2 = ResourcePermission.findOne(self._store, ResourcePermission('p2', 'r2'))
#        rp3 = ResourcePermission.findOne(self._store, ResourcePermission('p3', 'r3'))
#        
#        rp1.addRole('rp1role1')
#        rp2.addRole('rp2role1')
#        rp2.addRole('rp2role2')
#        rp3.addRole('rp3role1')
#        rp3.addRole('rp3role2')
#        rp3.addRole('rp3role3')
#        rp1.save(self._store)
#        rp2.save(self._store)
#        rp3.save(self._store)
#        
#        self._cache.createCollection(self._config.cache.cachedRolesCollection)
#        RBACSystemXMLRPC.RolesToCache(self._config, self._context)
#        
#        rp1Cache = self._cache.get(self._config.cache.cachedRolesCollection, 'r1|p1').split(',')
#        rp2Cache = self._cache.get(self._config.cache.cachedRolesCollection, 'r2|p2').split(',')
#        rp3Cache = self._cache.get(self._config.cache.cachedRolesCollection, 'r3|p3').split(',')
#        
#        self.assertEqual(1, len(rp1Cache))
#        self.assertEqual(2, len(rp2Cache))
#        self.assertEqual(3, len(rp3Cache))
#        
#        self.assertTrue('rp1role1' in rp1Cache)
#        self.assertTrue('rp2role1' in rp2Cache)
#        self.assertTrue('rp2role2' in rp2Cache)
#        self.assertTrue('rp3role1' in rp3Cache)
#        self.assertTrue('rp3role2' in rp3Cache)
#        self.assertTrue('rp3role3' in rp3Cache)
#        
#        