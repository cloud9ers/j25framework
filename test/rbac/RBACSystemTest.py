#import unittest
#import datetime
#import uuid
#from test.fixtures.MongoDBFixture import MongoDBFixture
#from test.fixtures.RemoteMemStoreFixture import RemoteMemStoreFixture
#from test.TestConfiguration import TestConfiguration
#from framework.CacheManagerImpl import CacheFactory
#from model.rbac.AuthToken import AuthToken
#from model.rbac.Role import Role
#from model.rbac.ResourcePermission import ResourcePermission
#from framework.security.RBACSystem import RBACSystem, NotFoundException,\
#    UnauthorizedException, AlreadyExistsException
#from framework.ModelLoader import AutoModelLoader 
#from model.rbac.AuthUser import AuthUser
#from framework.model.Document import Document
#from framework.interfaces.DocumentStore import OID
#from services.RBACSystemXMLRPC import RBACSystemXMLRPC
#from framework import Context
#from framework.security.Crypto import Crypto
#from framework.stores.MongoStore import MongoStore
#import random
#
#_mongodb = None
#
#def setUpModule(module):
#    module._mongodb  = MongoDBFixture()
#    module._mongodb.setUp()
#    
#def tearDownModule(module):
#    module._mongodb.tearDown()
#
#
#class SessionMock(dict):
#    def __init__(self):
#        self['userID'] = 'admin'
#        
#    def __getattr__(self, key):
#        return self[key]
#    
#    def invalidate(self):
#        self['userID'] = None
#
#class RBACSystemTest(unittest.TestCase):
#    
#    def setUp(self):
#        import model
#        AutoModelLoader(model)
#        self._memcachedServer = RemoteMemStoreFixture()
#        self._memcachedServer.setUp()
#        self._config = TestConfiguration.createInstance()
#        self._store = MongoStore("%s%s" % ("db", str(random.randint(1, 1000))),
#                                self._config.store.auto_create_collections,
#                                self._config.store.ip,
#                                int(self._config.store.port),
#                                0.5*1024*1024)
#        self._cache = CacheFactory.createInstance(self._config)
#        self._context = Context.ContextFactory.createContext(self._config, None)
#        
#    def tearDown(self):
#        self._memcachedServer.tearDown()
#        self._store = None
#        self._cache = None
#        self._context = None
#        self._config = None
#    
#    def _createAdminUser(self):
#        # add admin      
#        AuthUser('admin', 'pass', None).save(self._store)
#        admin = AuthUser.findOne(self._store, AuthUser('admin', None, None))
#        admin.state = None
#        admin.save(self._store)
#        return admin
#        
#    def _addAdminRole(self, admin):
#        # create appropriate roles for admin 
#        role = Role('Ay haga')
#        role.isSuperAdmin = True
#        
#        roleID = str(role.save(self._store))        
#        admin.roleIDs = [roleID]
#        admin.save(self._store)
#        return roleID
#    
#    def testUpdateCachedPermissions(self):
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        
#        role1ID = str(Role('role1').save(self._store))
#        role2ID = str(Role('role2').save(self._store))
#        role3ID = str(Role('role3').save(self._store))
#        
#        rbac._updateCachedPermissions(role1ID, 'permission1', 'resource1', RBACSystem.ADD)
#        self._cache.createCollection(self._config.cache.cachedRolesCollection)
#        collection = self._config.cache.cachedRolesCollection
#        self.assertEquals(self._cache.get(collection, "permission1|resource1"), role1ID)
#        rbac._updateCachedPermissions(role2ID, 'permission1', 'resource1', RBACSystem.ADD)
#        result = self._cache.get(collection, "permission1|resource1").split(',')
#        self.assertEquals(sorted(result), sorted([role1ID, role2ID]))
#        
#        rbac._updateCachedPermissions(role2ID, 'permission1', 'resource1', RBACSystem.ADD)
#        result = self._cache.get(collection, "permission1|resource1").split(',')
#        self.assertEquals(sorted(result), sorted([role1ID, role2ID]))
#        
#        rbac._updateCachedPermissions(role1ID, 'permission1', 'resource1', RBACSystem.REVOKE)
#        result = self._cache.get(collection, "permission1|resource1").split(',')
#        self.assertEquals(sorted(result), sorted([role2ID]))
#        
#        rbac._updateCachedPermissions(role3ID, 'permission1', 'resource1', RBACSystem.ADD)
#        result = self._cache.get(collection, "permission1|resource1").split(',')
#        self.assertEquals(sorted(result), sorted([role3ID, role2ID]))
#                       
#    def testCreateInstance(self):
#        rbac = RBACSystem.createInstance(self._config, self._store, self._cache)
#        self.assertTrue(isinstance(rbac, RBACSystem))
#        
#    def testGenerateActivationToken(self):
#        user = AuthUser('user', 'pass', AuthUser.NEW)
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        activationToken = rbac._generateActivationToken(user)
#        self.assertTrue(isinstance(activationToken, basestring))
#    
#    def testRemoveActivationToken(self):
#        user = AuthUser('user', 'pass', AuthUser.NEW)
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        activationToken = rbac._generateActivationToken(user)
#        user.save(self._store)
#        user = AuthUser.findOne(self._store, AuthUser('user', 'pass', None))
#        self.assertEquals(user.tokens[0].token, activationToken)
#        
#        rbac._removeActivationToken(user, None)
#        user.save(self._store)
#        user = AuthUser.findOne(self._store, AuthUser('user', 'pass', None))
#        
#        self.assertFalse(user.tokens)
#        
#        activationToken = rbac._generateActivationToken(user)
#        user.save(self._store)
#        user = AuthUser.findOne(self._store, AuthUser('user', 'pass', None))
#        self.assertEquals(user.tokens[0].token, activationToken)
#        
#        rbac._removeActivationToken(user, activationToken)
#        user.save(self._store)
#        user = AuthUser.findOne(self._store, AuthUser('user', 'pass', None))        
#        self.assertFalse(user.tokens)
#        
#    def testGetRoleIfExists(self):
#        existsRoleID = str(Role('NewRole').save(self._store))
#        userID = str(AuthUser('Ali', 'pass', None).save(self._store))
#              
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        
#        self.assertEquals(rbac._getRoleIfExists(existsRoleID).roleName, 'NewRole')
#               
#        self.assertRaises(NotFoundException, rbac._getRoleIfExists, '33ddd')
#        self.assertRaises(NotFoundException, rbac._getRoleIfExists, userID)
#   
#        self.assertRaises(NotFoundException, rbac._getRoleIfExists, "4cfe65b8b95e595d24000004")
#        oid = Role('role1').save(self._store)
#        result = rbac._getRoleIfExists(str(oid))
#        self.assertTrue(isinstance(result , Role))
#        self.assertEqual(result.roleName , 'role1')
#        
#        
#    def testGetUserIfExists(self):
#        AuthUser('ali', 'password', AuthUser.NEW).save(self._store)
#        notExistsUserID = 'Fathy'
#       
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        
#        self.assertEquals(rbac._getUserIfExists('ali').userID, 'ali')
#        self.assertRaises(NotFoundException, rbac._getUserIfExists, notExistsUserID)
#        
#    def testGetOrCreateGuestRoleOID(self):
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        self.assertFalse(Role.findOne(self._store, Role(Role.DEFAULT)))
#        self.assertEquals(Role.count(self._store), 0)
#        
#        oid1 = rbac._getOrCreateGuestRoleOID()
#        self.assertTrue(Role.findOne(self._store, Role(Role.DEFAULT)))
#        self.assertEquals(Role.count(self._store), 1)
#        
#        oid2 = rbac._getOrCreateGuestRoleOID()
#        self.assertTrue(Role.findOne(self._store, Role(Role.DEFAULT)))
#        self.assertEquals(Role.count(self._store), 1)
#        
#        self.assertEquals(oid1, oid2)
#        
#        oid3 = rbac._getOrCreateGuestRoleOID()
#        self.assertTrue(Role.findOne(self._store, Role(Role.DEFAULT)))
#        self.assertEquals(Role.count(self._store), 1)
#        self.assertEquals(oid1, oid2)
#        self.assertEquals(oid2, oid3)
#            
#    def testAddGetDeleteUser(self):
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#        
#        admin = AuthUser.findOne(self._store, AuthUser('admin', None, None))                                 
#        self.assertFalse(admin.state)
#        
#        # CREATE resources and permissions required to pass the check and checkSession
#        rp = ResourcePermission(RBACSystem.ACTIVATE, RBACSystem.USER)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.GET, RBACSystem.USER)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.USER)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.DELETE, RBACSystem.USER)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        #create a session for admin
#        session = {'userID':'admin'}
#
#        token = rbac.addUser("fawzy", "mypassword", session)
#        self.assertTrue(isinstance(token, str))
#        user = AuthUser.findOne(self._store, Document({'userID': 'fawzy'}))
#        self.assertTrue(user != None)
#        self.assertTrue(isinstance(user, AuthUser))
#        self.assertEqual(user.state, AuthUser.NEW)
#        self.assertTrue(user.tokens)
#        self.assertEqual(len(user.tokens), 1)
#        self.assertTrue(isinstance(user.tokens[0], AuthToken))
#        self.assertEqual(user.tokens[0].token, token)
#        self.assertEqual(user.tokens[0].purpose, AuthToken.ACTIVATE_ACCOUNT)
#        self.assertTrue(isinstance(user.tokens[0].generationDatetime, datetime.datetime))
#        now = datetime.datetime.now()
#        self.assertEqual(user.tokens[0].generationDatetime.day, now.day)
#        self.assertEqual(user.tokens[0].generationDatetime.year, now.year)
#        self.assertEqual(user.tokens[0].generationDatetime.month, now.month)
#        self.assertTrue(user.tokens[0].expirationDatetime > user.tokens[0].generationDatetime)
#        self.assertEqual((user.tokens[0].expirationDatetime - user.tokens[0].generationDatetime).days, self._config.main.default_expire_days)
#       
#        self.assertRaises(AlreadyExistsException, rbac.addUser, "fawzy", "password", session)
#        # Add another 2 users
#        rbac.addUser("helmy", "helmypassword", session)
#        helmyUser = AuthUser.findOne(self._store, Document({'userID': 'helmy'}))
#        helmyUser.state = None
#        helmyUser.save(self._store)
#        rbac.addUser("gamal", "gamalpassword", session)
#        self.assertEqual(4, AuthUser.count(self._store))
#        # Test getUser:
#        # Get 1st user, check type, & data
#        user1 = rbac.getUser('fawzy', session)
#        self.assertTrue(isinstance(user1, dict))
#        self.assertEqual(AuthUser.NEW, user1['state'])
#        self.assertTrue(isinstance(user1['tokens'], list))
#        self.assertTrue(isinstance(user1['tokens'][0], dict))
#        self.assertEqual(user1['tokens'][0]['token'], token)
#        # Test deleteUser:
#        # Delete the second user
#        self.assertTrue(rbac.deleteUser('helmy', session))
#        # records in database should be counted as 2
#        self.assertEqual(3, AuthUser.count(self._store))
#        # is user still in database?
#        self.assertFalse(AuthUser.findOne(self._store, Document({'userID': 'helmy'})))
#        # Other users should be there
#        self.assertTrue(AuthUser.findOne(self._store, Document({'userID': 'fawzy'})))
#        self.assertTrue(AuthUser.findOne(self._store, Document({'userID': 'gamal'})))
#        
#        self.assertFalse(rbac.deleteUser('Fathy', session))
#        self.assertFalse(rbac.deleteUser('helmy', session))
#    
#    def testAssignUnassignRoleToUser(self):
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#                
#        admin = AuthUser.findOne(self._store, AuthUser('admin', None, None))                                 
#        self.assertFalse(admin.state)
#        
#        # CREATE resources and permissions required to pass the check and checkSession 
#        rp = ResourcePermission(RBACSystem.ASSIGN, RBACSystem.ROLE)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.UNASSIGN, RBACSystem.ROLE)
#        rp.roles = [roleID]
#        rp.save(self._store)
#               
#        #create a session for admin
#        session = {'userID':'admin'}
#        
#        # Create 3 roles
#        role1 = Role('role1Name')
#        role1ID = str(role1.save(self._store))
#        role2 = Role('role2Name')
#        role2ID = str(role2.save(self._store))
#        role3 = Role('role3Name')
#        role3ID = str(role3.save(self._store))
#        # Add 2 users
#        AuthUser("fawzy", "fawzyPassword", AuthUser.NEW).save(self._store)
#        AuthUser("helmy", "helmyPassword", AuthUser.NEW).save(self._store)
#        # Add role to the first user & assert that the role was added
#        rbac.assignRoleToUser('fawzy', role1ID, session)
#        user1 = AuthUser.findOne(self._store, Document({'userID': 'fawzy'}))
#        self.assertTrue(isinstance(user1, AuthUser))
#        self.assertTrue(role1ID in user1.roleIDs)
#        # Assert that the same role could not be added twice
#        rbac.assignRoleToUser('fawzy', role1ID, session)
#        self.assertEqual(1, user1.roleIDs.count(role1ID))
#        # Assert the the added role was not added to the 2nd user
#        user2 = AuthUser.findOne(self._store, Document({'userID': 'helmy'}))
#        self.assertEqual(None, user2.roleIDs)
#        # Add another role to the 1st user & assert that the 2 added roles are there
#        rbac.assignRoleToUser('fawzy', role2ID, session)
#        user1 = AuthUser.findOne(self._store, Document({'userID': 'fawzy'}))
#        self.assertTrue(role1ID in user1.roleIDs)
#        self.assertTrue(role2ID in user1.roleIDs)
#        # Exceptions
#        self.assertRaises(NotFoundException, rbac.assignRoleToUser, 'fawzy', '4cfe65b8b95e595d24000004', session)
#        self.assertRaises(NotFoundException, rbac.assignRoleToUser, 'fakeName', role2ID, session)
#        
#        # Add role to 2nd user
#        rbac.assignRoleToUser('helmy', role3ID, session)
#        user2 = AuthUser.findOne(self._store, Document({'userID': 'helmy'}))
#        self.assertEqual(1, user2.roleIDs.count(role3ID))
#        # Remove 1st role from 1st user 7 assert
#        self.assertTrue(role1ID in user1.roleIDs)
#        rbac.unassignRoleFromUser('fawzy', role1ID, session)
#        user1 = AuthUser.findOne(self._store, Document({'userID': 'fawzy'}))
#        self.assertFalse(role1ID in user1.roleIDs)
#        # Remove 2nd role from 1st user
#        self.assertTrue(role2ID in user1.roleIDs)
#        self.assertEqual(1, len(user1.roleIDs))
#        rbac.unassignRoleFromUser('fawzy', role2ID, session)
#        user1 = AuthUser.findOne(self._store, Document({'userID': 'fawzy'}))
#        self.assertEqual(None, user1.roleIDs)
#        # Assert that the 2nd user was not affected
#        user2 = AuthUser.findOne(self._store, Document({'userID': 'helmy'}))
#        self.assertTrue(role3ID in user2.roleIDs)
#        self.assertEqual(1, len(user2.roleIDs))
#
#    def testAddRole(self):
#        rbac = RBACSystem(self._config, self._store, self._cache)
#                
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#        
#        admin = AuthUser.findOne(self._store, AuthUser('admin', None, None))                                 
#        self.assertFalse(admin.state)
#        
#        # CREATE resources and permissions required to pass the check and checkSession        
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.ROLE)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        #create a session for admin
#        session = {'userID':'admin'}
#        
#        oid = rbac.addRole(session, "role1")
#        self.assertTrue(oid)
#        self.assertTrue(isinstance(oid, OID))
#        
#        role = Role.findOne(self._store, Document({'roleName': 'role1'}))
#        self.assertTrue(role)
#
#    def testGetRoleByName(self):
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#        
#        admin = AuthUser.findOne(self._store, AuthUser('admin', None, None))                                 
#        self.assertFalse(admin.state)
#        
#        # CREATE resources and permissions required to pass the check and checkSession
#        
#        rp = ResourcePermission(RBACSystem.GET, RBACSystem.ROLE)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.ROLE)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        #create a session for admin
#        session = {'userID':'admin'}
#        
#        self.assertFalse(rbac.getRoleByName("anything", session))
#        oid = rbac.addRole(session, "role1")      
#        result = rbac.getRoleByName('role1', session)
#        self.assertEqual(result.getOID(), oid)
#        self.assertTrue(isinstance(result , Role))
#
#    def testGetAllRoles(self):
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#        
#        admin = AuthUser.findOne(self._store, AuthUser('admin', None, None))                                 
#        self.assertFalse(admin.state)
#        
#        # CREATE resources and permissions required to pass the check and checkSession
#        
#        rp = ResourcePermission(RBACSystem.GET, RBACSystem.ROLE)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.ROLE)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        #create a session for admin
#        session = {'userID':'admin'}
#        
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        rbac.addRole(session, "role1")  
#        rbac.addRole(session, "role2")
#        rbac.addRole(session, "role3")
#        roles = rbac.getAllRoles(session)
#        self.assertEqual(len(roles), 3)
#        
#    def testRenameDeleteRole(self):
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#        
#        admin = AuthUser.findOne(self._store, AuthUser('admin', None, None))                                 
#        self.assertFalse(admin.state)
#        
#        # CREATE resources and permissions required to pass the check and checkSession
#        
#        rp = ResourcePermission(RBACSystem.UPDATE, RBACSystem.ROLE)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.ROLE)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.GET, RBACSystem.ROLE)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.DELETE, RBACSystem.ROLE)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        #create a session for admin
#        session = {'userID':'admin'}
#        
#        oid1 = rbac.addRole(session, "role1")
#        oid2 = rbac.addRole(session, "role2")
#        rbac.renameRole(oid2, "myrole", session)
#        role = rbac._getRoleIfExists(str(oid2))
#        self.assertEquals(role.roleName, "myrole")
#        rbac.deleteRole(oid1, session)
#        self.assertEquals(len(rbac.getAllRoles(session)), 1)
#
#    def testUpdateRoleDescription(self):
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#        
#        admin = AuthUser.findOne(self._store, AuthUser('admin', None, None))                                 
#        self.assertFalse(admin.state)
#        
#        # CREATE resources and permissions required to pass the check and checkSession
#        
#        rp = ResourcePermission(RBACSystem.UPDATE, RBACSystem.ROLE)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.ROLE)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.GET, RBACSystem.ROLE)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.DELETE, RBACSystem.ROLE)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        #create a session for admin
#        session = {'userID':'admin'}
#        
#        oid1 = rbac.addRole(session, "role1")
#        rbac.updateRoleDescription(oid1, session, "first role")
#        role = Role.findOne(self._store, Role("role1"))
#        self.assertTrue(role != None)
#        self.assertEquals(role.description, "first role")
#                
#    def testGrantRevokePermission(self):
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#        # CREATE resources and permissions required to pass the check and checkSession
#        
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.PERMISSION)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.ROLE)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.REVOKE, RBACSystem.PERMISSION)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        #create a session for admin
#        session = {'userID':'admin'}
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        self._cache.createCollection(self._config.cache.cachedRolesCollection)
#        
#        oid0 = rbac.addRole(session, "role0")  
#        oid1 = rbac.addRole(session, "role1")
#        oid2 = rbac.addRole(session, "role2")
#       
#        rbac.grantPermission(str(oid0), "read", "rs1", session)
#        rbac.grantPermission(str(oid1), "read", "rs1", session)
#        rbac.grantPermission(str(oid2), "read", "rs1", session)
#        
#        rbac.grantPermission(str(oid0), "write", "rs1", session)
#        rbac.grantPermission(str(oid1), "write", "rs1", session)
#        
#        rbac.grantPermission(str(oid1), "exec", "rs1", session)
#        rbac.grantPermission(str(oid2), "exec", "rs1", session)
#        
#        results = ResourcePermission.find(self._store, ResourcePermission(None, None))
#        self.assertEqual(len(results), 6)
#        results.sort('permission')
#        
#        self.assertEquals(results[0].permission, 'add')
#        self.assertEquals(results[0].resource, 'permission')
#        self.assertEquals(sorted(results[0].roles), [roleID])
#        
#        self.assertEquals(results[1].permission, 'add')
#        self.assertEquals(results[1].resource, 'role')
#        self.assertEquals(sorted(results[1].roles), [roleID])
#                
#        self.assertEquals(results[2].permission, 'exec')
#        self.assertEquals(results[2].resource, 'rs1')
#        self.assertEquals(sorted(results[2].roles), sorted([str(oid1), str(oid2)]))
#                
#        self.assertEquals(results[3].permission, 'read')
#        self.assertEquals(results[3].resource, 'rs1')
#        self.assertEquals(sorted(results[3].roles), sorted([str(oid0), str(oid1), str(oid2)]))
#        
#        self.assertEquals(results[4].permission, 'revoke')
#        self.assertEquals(results[4].resource, 'permission')
#        self.assertEquals(sorted(results[4].roles), [roleID])
#
#        self.assertEquals(results[5].permission, 'write')
#        self.assertEquals(results[5].resource, 'rs1')
#        self.assertEquals(sorted(results[5].roles), sorted([str(oid0), str(oid1)]))
#                
#        # Test Cache
#        self.assertEquals(self._cache.get(self._config.cache.cachedRolesCollection, "read|rs1"), "%s,%s,%s" % (str(oid0), str(oid1), str(oid2)))
#        
#        # Test that cache doesn't add duplicated entries
#        rbac._updateCachedPermissions(str(oid0), "read", "rs1", session)
#        rbac._updateCachedPermissions(str(oid1), "read", "rs1", session)
#        rbac._updateCachedPermissions(str(oid2), "read", "rs1", session)
#        
#        self.assertEquals(self._cache.get(self._config.cache.cachedRolesCollection, "read|rs1"), "%s,%s,%s" % (str(oid0), str(oid1), str(oid2)))
#        
#        rbac.revokePermission(str(oid0), "read", "rs1", session)
#        results = ResourcePermission.find(self._store, ResourcePermission(None, None))
#        self.assertEqual(len(results), 6)
#        results.sort('permission')
#        
#        self.assertEquals(results[2].permission, 'exec')
#        self.assertEquals(results[2].resource, 'rs1')
#        self.assertEquals(sorted(results[2].roles), sorted([str(oid1), str(oid2)]))
#        
#        self.assertEquals(results[3].permission, 'read')
#        self.assertEquals(results[3].resource, 'rs1')
#        self.assertEquals(sorted(results[3].roles), sorted([str(oid1), str(oid2)]))
#        
#        # Test Cache
#        self.assertEquals(self._cache.get(self._config.cache.cachedRolesCollection, "read|rs1"), "%s,%s" % (str(oid1), str(oid2)))
#        self.assertEquals(len(self._cache.get(self._config.cache.cachedRolesCollection, "read|rs1").split(',')), 2)
#        
#        rbac.revokePermission(str(oid1), "read", "rs1", session)
#        
#        results = ResourcePermission.find(self._store, ResourcePermission(None, None))
#        self.assertEqual(len(results), 6)
#        results.sort('permission')
#        
#        self.assertEquals(results[2].permission, 'exec')
#        self.assertEquals(results[2].resource, 'rs1')
#        self.assertEquals(sorted(results[2].roles), sorted([str(oid1), str(oid2)]))
#        
#        self.assertEquals(results[3].permission, 'read')
#        self.assertEquals(results[3].resource, 'rs1')
#        self.assertEquals(sorted(results[3].roles), sorted([str(oid2)]))
#        
#        self.assertEquals(results[5].permission, 'write')
#        self.assertEquals(results[5].resource, 'rs1')
#        self.assertEquals(sorted(results[5].roles), sorted([str(oid0), str(oid1)]))
#        
#        # Test Cache
#        self.assertEquals(self._cache.get(self._config.cache.cachedRolesCollection, "read|rs1"), str(oid2))
#        self.assertEquals(len(self._cache.get(self._config.cache.cachedRolesCollection, "read|rs1").split(',')), 1)
#        
#        rbac.revokePermission(str(oid2), "read", "rs1", session)
#        
#        results = ResourcePermission.find(self._store, ResourcePermission(None, None))
#        self.assertEqual(len(results), 5)
#        results.sort('permission')
#        
#        self.assertEquals(results[2].permission, 'exec')
#        self.assertEquals(results[2].resource, 'rs1')
#        self.assertEquals(sorted(results[2].roles), sorted([str(oid1), str(oid2)]))
#        
#        self.assertEquals(results[4].permission, 'write')
#        self.assertEquals(results[4].resource, 'rs1')
#        self.assertEquals(len(results[4].roles), 2)
#        self.assertEquals(sorted(results[4].roles), sorted([str(oid0), str(oid1)]))
#        
#        # Test Cache
#        self.assertEquals(self._cache.get(self._config.cache.cachedRolesCollection, "exec|rs1"), "%s,%s" % (str(oid1), str(oid2)))
#        self.assertEquals(len(self._cache.get(self._config.cache.cachedRolesCollection, "exec|rs1").split(',')), 2)
#        
#        rbac.revokePermission(str(oid0), "write", "rs1", session)
#        
#        results = ResourcePermission.find(self._store, ResourcePermission(None, None))
#        self.assertEqual(len(results), 5)
#        results.sort('permission')
#        
#        self.assertEquals(results[2].permission, 'exec')
#        self.assertEquals(results[2].resource, 'rs1')
#        self.assertEquals(sorted(results[2].roles), sorted([str(oid1), str(oid2)]))
#        
#        self.assertEquals(results[4].permission, 'write')
#        self.assertEquals(results[4].resource, 'rs1')
#        self.assertEquals(len(results[4].roles), 1)
#        self.assertEquals(sorted(results[4].roles), sorted([str(oid1)]))
#                
#        # Test Cache
#        self.assertEquals(self._cache.get(self._config.cache.cachedRolesCollection, "write|rs1"), str(oid1))
#        self.assertEquals(len(self._cache.get(self._config.cache.cachedRolesCollection, "write|rs1").split(',')), 1)
#        
#        rbac.revokePermission(str(oid1), "write", "rs1", session)
#        
#        results = ResourcePermission.find(self._store, ResourcePermission(None, None))
#        self.assertEqual(len(results), 4)
#        results.sort('permission')
#        
#        self.assertEquals(results[2].permission, 'exec')
#        self.assertEquals(results[2].resource, 'rs1')
#        self.assertEquals(sorted(results[2].roles), sorted([str(oid1), str(oid2)]))
#                       
#        # Test Cache
#        self.assertEquals(self._cache.get(self._config.cache.cachedRolesCollection, "exec|rs1"), "%s,%s" % (str(oid1), str(oid2)))
#        self.assertEquals(len(self._cache.get(self._config.cache.cachedRolesCollection, "exec|rs1").split(',')), 2)
#        
#        rbac.revokePermission(str(oid1), "exec", "rs1", session)
#        
#        results = ResourcePermission.find(self._store, ResourcePermission(None, None))
#        self.assertEqual(len(results), 4)
#        results.sort('permission')
#        
#        self.assertEquals(results[2].permission, 'exec')
#        self.assertEquals(results[2].resource, 'rs1')
#        self.assertEquals(sorted(results[2].roles), [str(oid2)])
#                       
#        # Test Cache
#        self.assertEquals(self._cache.get(self._config.cache.cachedRolesCollection, "exec|rs1"), str(oid2))
#        self.assertEquals(len(self._cache.get(self._config.cache.cachedRolesCollection, "exec|rs1").split(',')), 1)
#        
#        rbac.revokePermission(str(oid2), "exec", "rs1", session)
#        
#        results = ResourcePermission.find(self._store, ResourcePermission(None, None))
#        self.assertEqual(len(results), 3)
#        results.sort('permission')                       
#        # Test Cache
#        self.assertRaises(KeyError, self._cache.get, self._config.cache.cachedRolesCollection, "exec|rs1")
#        
#        # Test roles added sorted:
#        
#        roleList = []
#        for i in range(100):
#            oid = Role('%s_%s' % ('role', str(i))).save(self._store)
#            roleList.append(str(oid))
#        
#        sortedRoleList = sorted(roleList)       
#        reversedRoleList = sorted(roleList, reverse=True)
#        self.assertNotEquals(sortedRoleList, reversedRoleList)
#        rp = ResourcePermission('Ay_Permission', 'Ay_Resource')
#        for role in reversedRoleList:
#            rp.addRole(role)
#        rp.save(self._store)
#        
#        rp = ResourcePermission.findOne(self._store, ResourcePermission('Ay_Permission', 'Ay_Resource'))
#        self.assertEquals(rp.roles, sortedRoleList)
#        
#        roleListWithRepeats = ['1', '10', '5', '4', '7', '2', '8', '3', '6', '0', '9', '9', '4', '5', '3', '4', '3']
#        roleList = ['1', '10', '5', '4', '7', '2', '8', '3', '6', '0', '9']
#        
#        sortedRoleList = sorted(roleList)       
#        reversedRoleList = sorted(roleList, reverse=True)
#        self.assertNotEquals(sortedRoleList, reversedRoleList)
#        rp = ResourcePermission('Ay_Permission2', 'Ay_Resource2')
#        for role in roleListWithRepeats:
#            rp.addRole(role)
#        rp.save(self._store)
#        
#        rp = ResourcePermission.findOne(self._store, ResourcePermission('Ay_Permission2', 'Ay_Resource2'))
#        self.assertEquals(rp.roles, sortedRoleList)
#        self.assertNotEquals(rp.roles, reversedRoleList)
#        self.assertNotEquals(rp.roles, roleList)
#        self.assertNotEquals(rp.roles, roleListWithRepeats)    
#       
#    def testSetGetUserState(self):        
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#        
#        # CREATE resources and permissions required to pass the check and checkSession
#        
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.USER)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.GET, RBACSystem.USER)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.UPDATE, RBACSystem.USER)
#        rp.roles = [roleID]
#        rp.save(self._store)
#                
#        #create a session for admin
#        session = {'userID':'admin'}
#        
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        rbac.addUser('mohamed', 'sss3222', session)
#        self.assertTrue(rbac.getUser('mohamed', session))
#        
#        self.assertEquals(rbac.getUserState('mohamed', session), 'new')
#        self.assertTrue(rbac.setUserState('mohamed', 'suspended', session))
#        self.assertTrue(rbac.getUser('mohamed', session))
#       
#        self.assertEquals(rbac.getUserState('mohamed', session), 'suspended')
#                
#        self.assertTrue(rbac.setUserState('mohamed', 'spam', session))
#        self.assertEquals(rbac.getUserState('mohamed', session), 'spam')             
#        
#        self.assertTrue(rbac.setUserState('mohamed', None, session))
#        self.assertFalse(rbac.getUserState('mohamed', session))
#        
#    def testActivateUser(self):
#        rbac = RBACSystem(self._config, self._store, self._cache)
#                
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#        
#        # CREATE resources and permissions required to pass the check and checkSession
#        rp = ResourcePermission(RBACSystem.ACTIVATE, RBACSystem.USER)
#        rp.roles = [roleID]
#        
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.GET, RBACSystem.USER)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.USER)
#        rp.roles = [roleID]
#        rp.save(self._store)
#        
#        #create a session for admin
#        session = {'userID':'admin'}
#                
#        activationToken = rbac.addUser('Ali', '1234#%', session)
#        user = AuthUser.findOne(self._store, AuthUser('Ali', None, None))
#        self.assertTrue(user.tokens)
#        self.assertTrue(isinstance(user.tokens[0], AuthToken))
#        self.assertEquals(user.state,AuthUser.NEW)
#        self.assertTrue(rbac.activateUser('Ali', activationToken=activationToken))
#        user = AuthUser.findOne(self._store, AuthUser('Ali', None, None))
#        self.assertTrue(user.state is None)
#        self.assertFalse(user.tokens)
#        
#        # Add a user to be activated by super admin's session
#        rbac.addUser('Ahmed', '1234#%', session)
#                        
#        userAhmed = AuthUser.findOne(self._store, AuthUser('Ahmed', None, None))
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        
#        self.assertTrue(userAhmed.tokens)
#        self.assertTrue(isinstance(userAhmed.tokens[0], AuthToken))
#        
#        self.assertTrue(rbac.activateUser('Ahmed', session=session))
#        
#        ahmedUser = AuthUser.findOne(self._store, AuthUser('Ahmed', None, None))
#        self.assertTrue(ahmedUser.state is None)
#        self.assertFalse(ahmedUser.tokens)      
#                
#        # adding user using admin session
#        rbac.addUser('Fahmy', '1234#%', session)
#        user = AuthUser.findOne(self._store, AuthUser('Fahmy', None, None))
#        self.assertTrue(user.tokens)
#        self.assertTrue(isinstance(user.tokens[0], AuthToken))
#        self.assertEquals(user.state, AuthUser.NEW)
#        
#        # using a session for a user with no sufficient previlleges
#        session = {'userID':'Ahmed'}
#        self.assertRaises(UnauthorizedException, rbac.activateUser, 'Fahmy', session=session)
#
#    def testDestroySession(self):
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#        
#        # CREATE resources and permissions required to pass the check and checkSession
#
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.USER)
#        rp.roles = [roleID]
#        rp.save(self._store)
#                    
#        session = SessionMock()
#        self.assertTrue(session['userID'])
#        rbac.addUser('Ali', '1234#%', session)
#        rbac.destroySession(session)
#        self.assertFalse(session['userID'])
#
#    def testCheckSession(self):
#        rbac = RBACSystem(self._config, self._store, self._cache)        
#        AuthUser('admin', '$78654#%', AuthUser.NEW).save(self._store)
#        
#        AuthUser('unAuthorized', 'ddvdv#%', AuthUser.NEW).save(self._store)
#        
#        roleID = str(Role('superAdmin').save(self._store))
#        
#        adminSession = {'userID':'admin'}
#        normalSession = {'userID':'unAuthorized'}
#        
#        admin = AuthUser.findOne(self._store, Document({'userID':'admin'}))
#        admin.assignRole(roleID)
#        admin.state = None
#        admin.save(self._store)
# 
#        rp = ResourcePermission(RBACSystem.ACTIVATE, RBACSystem.USER)
#        rp.addRole(roleID)
#        rp.save(self._store)
#        self.assertTrue(rbac._checkSession(adminSession, RBACSystem.ACTIVATE, RBACSystem.USER))
#        self.assertRaises(UnauthorizedException, rbac._checkSession, normalSession, RBACSystem.ACTIVATE, RBACSystem.USER)
#        
#    def testGetUsersByRole(self):
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        # Add 3 roles
#        role1 = Role('role1Name')
#        role1ID = str(role1.save(self._store))
#        role2 = Role('role2Name')
#        role2ID = str(role2.save(self._store))
#        role3 = Role('role3Name')
#        role3ID = str(role3.save(self._store))
#        # Add 4 users
#        AuthUser("fawzy", "fawzyPassword", AuthUser.NEW).save(self._store)
#        user1 = AuthUser.findOne(self._store, Document({'userID': 'fawzy'}))
#        AuthUser("helmy", "helmyPassword", AuthUser.NEW).save(self._store)
#        user2 = AuthUser.findOne(self._store, Document({'userID': 'helmy'}))
#
#        AuthUser("manal", "manalpassword", AuthUser.NEW).save(self._store)
#        user4 = AuthUser.findOne(self._store, Document({'userID': 'manal'}))
#        # Add 1st role to 1st user
#        user1.assignRole(role1ID)
#        user1.save(self._store)
#        # Add 2nd role to 1st user
#        user1.assignRole(role2ID)
#        user1.save(self._store)
#        # Add 2nd role to 2nd user
#        user2.assignRole(role2ID)
#        user2.save(self._store)
#        # Add 3rd role to 2nd user
#        user2.assignRole(role3ID)
#        user2.save(self._store)
#        # Add 3rd role to 4th user
#        user4.assignRole(role3ID)
#        user4.save(self._store)
#        
#        session = {'userID':'admin'}
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#        
#        rp = ResourcePermission(RBACSystem.GET, RBACSystem.USER)
#        rp.addRole(roleID)
#        rp.save(self._store)
#        
#        # Get users in 1st role, should be: fawzy
#        users = rbac.getUsersByRole(role1ID, session)
#        self.assertTrue(isinstance(users, list))
#        self.assertEqual(1, len(users))
#        self.assertTrue('fawzy' in users)
#        # Get users in 2nd role, should be: fawzy & helmy
#        users = rbac.getUsersByRole(role2ID, session)
#        self.assertTrue(isinstance(users, list))
#        self.assertEqual(2, len(users))
#        self.assertTrue('fawzy' in users)
#        self.assertTrue('helmy' in users)
#        # Get users in 3rd role, should be: helmy & manal, Gamal shouldn't be in
#        users = rbac.getUsersByRole(role3ID, session)
#        self.assertTrue(isinstance(users, list))
#        self.assertEqual(2, len(users))
#        self.assertTrue('helmy' in users)
#        self.assertTrue('manal' in users)
#        self.assertFalse('gamal' in users)
#        # If given role is not in database, an empty list should be returned
#        self.assertRaises(NotFoundException, rbac.getUsersByRole, 'neverExist', session)
#    
#    def testCheckPassword(self):
#        session = {'userID':'admin'}
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#        
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.USER)
#        rp.addRole(roleID)
#        rp.save(self._store)
#        
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        # Create 2 users
#        rbac.addUser('fawzy', 'fawzyPassword', session)
#        rbac.addUser('helmy', 'helmyPassword', session)
#        
#        self.assertTrue(rbac.checkPassword('fawzy', 'fawzyPassword'))
#        self.assertFalse(rbac.checkPassword('fawzy', 'fakePassword'))
#        self.assertFalse(rbac.checkPassword('helmy', 'fawzyPassword'))
#        self.assertTrue(rbac.checkPassword('helmy', 'helmyPassword'))
#        self.assertFalse(rbac.checkPassword('fakeUser', 'fawzyPassword'))
#    
#    def testResetUserPassword(self):
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        session = {'userID':'admin'}
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#        
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.USER)
#        rp.addRole(roleID)
#        rp.save(self._store)
#                
#        rp = ResourcePermission(RBACSystem.RESET, RBACSystem.PASSWORD)
#        rp.addRole(roleID)
#        rp.save(self._store)
#        
#        rbac.addUser('fawzy', 'fawzyPassword', session)
#        user1 = AuthUser.findOne(self._store, Document({'userID': 'fawzy'}))
#        initialTokensCount1 = len(user1.tokens)
#        rbac.addUser('helmy', 'helmyPassword', session)
#        user2 = AuthUser.findOne(self._store, Document({'userID': 'helmy'}))
#        initialTokensCount2 = len(user2.tokens)
#        
#        token = rbac.resetUserPassword('fawzy', session)
#        self.assertTrue(isinstance(token, str))
#        user1 = AuthUser.findOne(self._store, Document({'userID': 'fawzy'}))
#        self.assertEqual(initialTokensCount1+1, len(user1.tokens))
#        
#        user2 = AuthUser.findOne(self._store, Document({'userID': 'helmy'}))
#        self.assertEqual(initialTokensCount2, len(user2.tokens))
#        
#        anyToken = uuid.uuid4().hex
#        self.assertEqual(len(anyToken), len(token))
#        
#        self.assertEqual(token, user1.tokens[-1].token)
#    
#    def testAuthenticate(self):
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        session = SessionMock()
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#        
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.USER)
#        rp.addRole(roleID)
#        rp.save(self._store)
#        rbac.addUser('fawzy', 'fawzyPassword', session)
#        user1 = AuthUser.findOne(self._store, Document({'userID': 'fawzy'}))
#        user1.state = None
#        user1.save(self._store)
#        rbac.addUser('helmy', 'helmyPassword', session)
#        user2 = AuthUser.findOne(self._store, Document({'userID': 'helmy'}))
#        user2.state = AuthUser.DISABLED
#        user2.save(self._store)
#        
#        self.assertTrue(rbac.authenticate('fawzy', 'fawzyPassword', session))
#        self.assertFalse(rbac.authenticate('fawzy', 'fakePassword', session))
#        self.assertFalse(rbac.authenticate('fawzy', 'fakePassword', session))
#        self.assertFalse(rbac.authenticate('helmy', 'helmyPassword', session))
#        self.assertFalse(rbac.authenticate('fakeUser', 'fakePassword', session))
#    
#    def testCheck(self):
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        role1OIDObject = Role('role1').save(self._store)
#        role2OIDObject = Role('role2').save(self._store)
#        role3OIDObject = Role('role3').save(self._store)
#        role4OIDObject = Role('role4').save(self._store)
#        
#        role1OID = str(role1OIDObject)
#        role2OID = str(role2OIDObject)
#        role3OID = str(role3OIDObject)
#        role4OID = str(role4OIDObject)
#        
#        document = ResourcePermission('permission1', 'resource1')
#        document.roles.append(role1OID)
#        document.save(self._store)
#        document = ResourcePermission('permission2', 'resource2')
#        document.roles.append(role1OID)
#        document.save(self._store)
#        document = ResourcePermission('permission3', 'resource3')
#        document.roles.append(role2OID)
#        document.save(self._store)
#        document = ResourcePermission('permission4', 'resource1')
#        document.roles.append(role2OID)
#        document.save(self._store)
#        document = ResourcePermission('permission5', 'resource2')
#        document.roles.append(role3OID)
#        document.save(self._store)
#        document = ResourcePermission('permission6', 'resource3')
#        document.roles.append(role3OID)
#        document.save(self._store)
#        
#        self._cache.createCollection(self._config.cache.cachedRolesCollection)
#        RBACSystemXMLRPC.RolesToCache(self._config, self._context)
#        
#        AuthUser("fawzy", "fawzyPassword", AuthUser.NEW).save(self._store)
#        user1 = AuthUser.findOne(self._store, Document({"userID":"fawzy"}))
#        del user1.state
#        AuthUser("helmy", "helmyPassword", AuthUser.NEW).save(self._store)
#        user2 = AuthUser.findOne(self._store, Document({"userID":"helmy"}))
#        del user2.state
#        AuthUser("manal", "manalPassword", AuthUser.NEW).save(self._store)
#        user3 = AuthUser.findOne(self._store, Document({"userID":"manal"}))
#        del user3.state
#        
#        user1.roleIDs = [role1OID]
#        user1.save(self._store)
#        
#        self.assertTrue(rbac.check('fawzy', 'permission1', 'resource1'))
#        self.assertTrue(rbac.check('fawzy', 'permission2', 'resource2'))
#        self.assertFalse(rbac.check('fawzy', 'permission1', 'resource2'))
#        self.assertFalse(rbac.check('fawzy', 'permission3', 'resource3'))
#        self.assertFalse(rbac.check('fawzy', 'fakePermission', 'FakeResource'))
#        self.assertFalse(rbac.check('helmy', 'permission1', 'resource1'))
#        self.assertFalse(rbac.check('helmy', 'permission2', 'resource2'))
#        self.assertFalse(rbac.check('helmy', 'permission3', 'resource3'))
#        self.assertFalse(rbac.check('helmy', 'permission6', 'resource3'))
#        self.assertFalse(rbac.check('helmy', 'permission3', 'resource3'))
#        self.assertFalse(rbac.check('helmy', 'fakePermission', 'FakeResource'))
#        
#        user3.roleIDs = [role1OID, role3OID]
#        user3.save(self._store)
#
#        self.assertTrue(rbac.check('fawzy', 'permission1', 'resource1'))
#        self.assertTrue(rbac.check('fawzy', 'permission2', 'resource2'))
#        self.assertFalse(rbac.check('fawzy', 'permission4', 'resource1'))
#        self.assertFalse(rbac.check('fawzy', 'permission5', 'resource2'))
#        
#        self.assertTrue(rbac.check('manal', 'permission1', 'resource1'))
#        self.assertTrue(rbac.check('manal', 'permission2', 'resource2'))
#        self.assertTrue(rbac.check('manal', 'permission5', 'resource2'))
#        self.assertTrue(rbac.check('manal', 'permission6', 'resource3'))
#        
#        self.assertFalse(rbac.check('helmy', 'permission1', 'resource1'))
#        self.assertFalse(rbac.check('helmy', 'permission2', 'resource2'))
#        self.assertFalse(rbac.check('helmy', 'permission3', 'resource3'))
#        self.assertFalse(rbac.check('helmy', 'permission6', 'resource3'))
#        self.assertFalse(rbac.check('helmy', 'permission3', 'resource3'))
#        
#        user2.roleIDs = [role4OID]
#        user2.save(self._store)
#        
#        self.assertFalse(rbac.check('helmy', 'permission1', 'resource1'))
#        self.assertFalse(rbac.check('helmy', 'permission2', 'resource2'))
#        self.assertFalse(rbac.check('helmy', 'permission3', 'resource3'))
#        self.assertFalse(rbac.check('helmy', 'permission4', 'resource1'))
#        self.assertFalse(rbac.check('helmy', 'permission5', 'resource2'))
#        self.assertFalse(rbac.check('helmy', 'permission6', 'resource3'))
#        
#        user1.state = 'anyState'
#        user1.save(self._store)
#        
#        self.assertFalse(rbac.check('fawzy', 'permission1', 'resource1'))
#        self.assertFalse(rbac.check('fawzy', 'permission2', 'resource2'))
#        self.assertFalse(rbac.check('fawzy', 'permission4', 'resource1'))
#        self.assertFalse(rbac.check('fawzy', 'permission5', 'resource2'))
#        
#        AuthUser("fawzy", "fawzyPassword", AuthUser.NEW).save(self._store)
#        user1 = AuthUser.findOne(self._store, Document({"userID":"fawzy"}))
#        del user1.state
#        
#        user1.roleIDs = [role1OID]
#        user1.save(self._store)
#        
#        ResourcePermission.remove(self._store, ResourcePermission('permission1', 'resource1'))
#        ResourcePermission.remove(self._store, ResourcePermission('permission2', 'resource2'))
#        ResourcePermission.remove(self._store, ResourcePermission('permission1', 'resource2'))
#        ResourcePermission.remove(self._store, ResourcePermission('permission3', 'resource3'))
#        
#        self.assertTrue(rbac.check('fawzy', 'permission1', 'resource1'))
#        self.assertTrue(rbac.check('fawzy', 'permission2', 'resource2'))
#        self.assertFalse(rbac.check('fawzy', 'permission1', 'resource2'))
#        self.assertFalse(rbac.check('fawzy', 'permission3', 'resource3'))
#        self.assertFalse(rbac.check('fawzy', 'fakePermission', 'FakeResource'))
#        
#        self._cache.delete(self._config.cache.cachedRolesCollection, 'resource1|permission1')
#        self._cache.delete(self._config.cache.cachedRolesCollection, 'resource2|permission2')
#        self._cache.delete(self._config.cache.cachedRolesCollection, 'resource3|permission3')
#        self._cache.delete(self._config.cache.cachedRolesCollection, 'resource1|permission4')
#        self._cache.delete(self._config.cache.cachedRolesCollection, 'resource2|permission5')
#        self._cache.delete(self._config.cache.cachedRolesCollection, 'resource3|permission6')
#    
#    def testChangePassword(self):
#        session = SessionMock()
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#        
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.USER)
#        rp.addRole(roleID)
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.UPDATE, RBACSystem.USER)
#        rp.addRole(roleID)
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.UPDATE, RBACSystem.PASSWORD)
#        rp.addRole(roleID)
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.PERMISSION)
#        rp.addRole(roleID)
#        rp.save(self._store)
#        
#        rbac.addUser('fawzy', 'fawzyPassword', session)
#        user = AuthUser.findOne(self._store, Document({"userID":"fawzy"}))
#        user.state = None
#        
#        # super admin Can do anything
#        result = rbac.changePassword(session, 'fawzy', 'fawzyNewPassword', 'fakePassword')
#        self.assertTrue(result)
#        result = rbac.changePassword(session, 'fawzy', 'fawzyNewPassword', 'fawzyPassword')
#        self.assertTrue(result)
#                        
#        newPasswordEncrypted = Crypto.encrypt(self._config, 'fawzyNewPassword', self._config.main.default_crypto_algorithm)
#        user = AuthUser.findOne(self._store, Document({'userID': 'fawzy'}))
#        self.assertEqual(newPasswordEncrypted, user.password)
#        
#        rbac.addUser('helmy', 'helmyPassword', session)
#        user = AuthUser.findOne(self._store, Document({"userID":"helmy"}))
#        user.state = None
#        authToken = AuthToken.createInstance(AuthToken.RESET_PASSWORD, 30)
#        user.tokens.append(authToken)
#        user.save(self._store)
#        
#        rbac.addUser('hany', 'hanypassword', session)
#        hanyUser = AuthUser.findOne(self._store, AuthUser('hany', None, None))
#        hanyUser.state = None
#        authToken = AuthToken.createInstance(AuthToken.RESET_PASSWORD, 30)
#        hanyUser.tokens.append(authToken)
#        hanyUser.save(self._store)
#        
#        # super admin Can do anything
#        result = rbac.changePassword(session, 'helmy', 'helmyNewPassword', 'fakeToken')
#        self.assertTrue(result)
#        result = rbac.changePassword(session, 'helmy', 'helmyNewPassword', None, authToken.token)
#        self.assertTrue(result)
#        
#        newPasswordEncrypted = Crypto.encrypt(self._config, 'helmyNewPassword', self._config.main.default_crypto_algorithm)
#        user = AuthUser.findOne(self._store, Document({'userID': 'helmy'}))
#        self.assertEqual(newPasswordEncrypted, user.password)
#        
#        # Test with unauthorized user session
#        
#        roleID = str(Role('new_role').save(self._store))
#        
#        unauthorizedUser = AuthUser('unauthorized', 'pass', None)
#        unauthorizedUser.roleIDs = [roleID]
#        unauthorizedUser.save(self._store)
#        
#        rbac.grantPermission(roleID, RBACSystem.UPDATE, RBACSystem.PASSWORD, session)
#        self.assertTrue(rbac.check('unauthorized', RBACSystem.UPDATE, RBACSystem.PASSWORD))
#        rbac.grantPermission(roleID, RBACSystem.UPDATE, RBACSystem.PASSWORD, session)
#        self.assertTrue(rbac.check('unauthorized', RBACSystem.UPDATE, RBACSystem.PASSWORD))
#        # Rest fawzy password to "fawzyPassword"
#        result = rbac.changePassword(session, 'fawzy', 'fawzyPassword', 'fawzyPassword')
#        self.assertTrue(result)
#        
#        # create session for unauthorized user
#        session = SessionMock()
#        session['userID'] = 'unauthorized'
#                
#        result = rbac.changePassword(session, 'fawzy', 'fawzyNewPassword', 'fakePassword')
#        self.assertFalse(result)
#       
#        result = rbac.changePassword(session, 'fawzy', 'fawzyNewPassword', 'fawzyPassword')
#        self.assertTrue(result)  
#        
#        newPasswordEncrypted = Crypto.encrypt(self._config, 'fawzyNewPassword', self._config.main.default_crypto_algorithm)
#        user = AuthUser.findOne(self._store, Document({'userID': 'fawzy'}))
#        self.assertEqual(newPasswordEncrypted, user.password)
#        
#        # Test password can't be changed if authToken expired
#        
#        authToken = AuthToken.createInstance(AuthToken.RESET_PASSWORD, 30)
#        authToken.expirationDatetime = datetime.datetime.now() + datetime.timedelta(days=-31)
#        hanyUser.tokens = [authToken]
#        hanyUser.save(self._store)
#        result = rbac.changePassword(session, 'hany', 'hanyNewPass', None, authToken.token)
#        self.assertFalse(result)
#        
#        authToken = AuthToken.createInstance(AuthToken.RESET_PASSWORD, 30)
#        authToken.expirationDatetime = datetime.datetime.now() + datetime.timedelta(days=-30)
#        hanyUser.tokens = [authToken]
#        hanyUser.save(self._store)
#
#        result = rbac.changePassword(session, 'hany', 'hanyNewPass', None, authToken.token)
#        self.assertFalse(result)
#
#        authToken = AuthToken.createInstance(AuthToken.RESET_PASSWORD, 30)
#        authToken.expirationDatetime = datetime.datetime.now() + datetime.timedelta(days=1)
#        hanyUser.tokens = [authToken]
#        hanyUser.save(self._store)
#        result = rbac.changePassword(session, 'hany', 'hanyNewPass', None, authToken.token)
#        self.assertTrue(result)
#
#        authToken = AuthToken.createInstance(AuthToken.RESET_PASSWORD, 30)
#        authToken.expirationDatetime = datetime.datetime.now() + datetime.timedelta(days=0)
#        hanyUser.tokens = [authToken]
#        hanyUser.save(self._store)
#        result = rbac.changePassword(session, 'hany', 'hanyNewPass', None, authToken.token)
#        self.assertFalse(result)
#        
#        
#        authToken = AuthToken.createInstance(AuthToken.RESET_PASSWORD, 30)
#        authToken.expirationDatetime = datetime.datetime.now() + datetime.timedelta(days=1)
#        hanyUser.tokens = [authToken]
#        hanyUser.save(self._store)
#        result = rbac.changePassword(session, 'hany', 'hanyNewPass', None, authToken.token)
#        self.assertTrue(result)
#        
#        # no tokens in user object, since token has been removed
#        result = rbac.changePassword(session, 'hany', 'hanyNewPass', None, authToken.token)
#        self.assertFalse(result)
#        
#    def testDeleteRole(self):
#        session = SessionMock()
#        admin = self._createAdminUser()        
#        roleID = self._addAdminRole(admin)
#        
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        rp = ResourcePermission(RBACSystem.ASSIGN, RBACSystem.ROLE)
#        rp.addRole(roleID)
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.USER)
#        rp.addRole(roleID)
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.PERMISSION)
#        rp.addRole(roleID)
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.ACTIVATE, RBACSystem.USER)
#        rp.addRole(roleID)
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.DELETE, RBACSystem.ROLE)
#        rp.addRole(roleID)
#        rp.save(self._store)
#        
#        
#        # Create 3 roles
#        role1 = Role('role1Name')
#        role1ID = str(role1.save(self._store))
#        role2 = Role('role2Name')
#        role2ID = str(role2.save(self._store))
#        
#        # Add 2 users
#        AuthUser("fawzy", "fawzyPassword", AuthUser.NEW).save(self._store)
#        AuthUser("helmy", "helmyPassword", AuthUser.NEW).save(self._store)
#        # Add role to the first user & assert that the role was added
#        rbac.assignRoleToUser('fawzy', role1ID, session)
#        rbac.assignRoleToUser('fawzy', role2ID, session)
#        
#        rbac.assignRoleToUser('helmy', role1ID, session)
#        rbac.assignRoleToUser('helmy', role2ID, session)
#        
#        rbac.grantPermission(role1ID, RBACSystem.ACTIVATE, RBACSystem.USER, session)
#        rbac.grantPermission(role1ID, RBACSystem.ADD, RBACSystem.USER, session)
#        
#        rbac.grantPermission(role2ID, RBACSystem.ACTIVATE, RBACSystem.USER, session)
#        
#        resourcePermissions = ResourcePermission.find(self._store, Document({'roles':role1ID}))
#        resourcePermissions2 = ResourcePermission.find(self._store, Document({'roles':role2ID}))
#
#        self.assertEquals(resourcePermissions.count(), 2)
#        self.assertEquals(resourcePermissions2.count(), 1)
#        
#        user1 = AuthUser.findOne(self._store, Document({'userID': 'fawzy'}))
#        
#        self.assertEquals(sorted(user1.roleIDs), sorted([role1ID, role2ID]))
#        
#        rbac.deleteRole(role1ID, session)
#        
#        fawzy = AuthUser.findOne(self._store, Document({'userID': 'fawzy'}))
#        self.assertTrue(sorted(fawzy.roleIDs), sorted([role2ID]))
#        
#        resourcePermissions = ResourcePermission.find(self._store, Document({'roles':role1ID}))
#        resourcePermissions2 = ResourcePermission.find(self._store, Document({'roles':role2ID}))
#            
#        self.assertEquals(resourcePermissions.count(), 0)
#        self.assertEquals(resourcePermissions2.count(), 1)
#        
#        cachedPermissions =  self._cache.get(self._config.cache.cachedRolesCollection, "%s|%s" % (RBACSystem.ACTIVATE, RBACSystem.USER))
#        self.assertRaises(KeyError, self._cache.get, self._config.cache.cachedRolesCollection, "%s|%s" % (RBACSystem.ADD, RBACSystem.USER))
#        self.assertTrue(role1ID not in cachedPermissions)
#        
#    def testGetEffectivePermissions(self):
#        rbac = RBACSystem(self._config, self._store, self._cache)
#        # Create 3 roles
#        role1 = Role('role1Name')
#        role1ID = str(role1.save(self._store))
#        role2 = Role('role2Name')
#        role2ID = str(role2.save(self._store))
#     
#        # Add 2 users
#        user1 = AuthUser("fawzy", "fawzyPassword", AuthUser.NEW)
#        user2 = AuthUser("helmy", "helmyPassword", AuthUser.NEW)
#        # Add role to the first user & assert that the role was added
#        user1.roleIDs = [role1ID, role2ID]
#        user1.save(self._store)
#        
#        user2.roleIDs = [role1ID, role2ID]
#        user2.save(self._store)
#                
#        # Add permission/resources and assign them to users
#        rp = ResourcePermission(RBACSystem.ACTIVATE, RBACSystem.USER)
#        rp2 = ResourcePermission(RBACSystem.ADD, RBACSystem.USER)
#        rp3 = ResourcePermission(RBACSystem.DELETE, RBACSystem.USER)
#        
#        rp.roles = [role1ID, role2ID]
#        rp2.roles = [role1ID]
#        rp3.roles = []
#        
#        rp.save(self._store)
#        rp2.save(self._store)        
#        rp3.save(self._store)
#                
#        self.assertTrue(sorted(rbac.getEffectivePermissions('fawzy')), sorted([(RBACSystem.USER, RBACSystem.ACTIVATE), (RBACSystem.USER, RBACSystem.ADD)]))
#        self.assertTrue(sorted(rbac.getEffectivePermissions('helmy')), [(RBACSystem.USER, RBACSystem.ACTIVATE)])
#        
#        #assign role to the new resource permission
#        #Re-assign user1 new that role
#        rp3.roles = [role1ID]
#        rp3.save(self._store)
#        user1.roleIDs = [role1ID]
#        user1.save(self._store)
#        
#        self.assertTrue(sorted(rbac.getEffectivePermissions('fawzy')), (RBACSystem.USER, RBACSystem.DELETE))
#
#    