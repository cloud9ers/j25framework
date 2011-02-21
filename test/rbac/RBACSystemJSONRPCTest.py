#import unittest
#import simplejson
#import httplib2
#
#from model.rbac.Role import Role
#from model.rbac.AuthUser import AuthUser
#from test.TestConfiguration import TestConfiguration
#from framework.stores.StoreFactory import MongoStoreFactory
#from framework.security.Crypto import Crypto
#from model.rbac.ResourcePermission import ResourcePermission
#from framework.security.RBACSystem import RBACSystem
#from test.fixtures.MongoDBFixture import MongoDBFixture
#from test.fixtures.AppServerFixture import AppServerFixture
#from test.fixtures.RemoteMemStoreFixture import RemoteMemStoreFixture
#
#_appServerFixture = None
#_mongo = None
#
#def setUpModule(module):
#    module._appServerFixture  = AppServerFixture()
#    module._appServerFixture.setUp()
#    module._mongo = MongoDBFixture()
#    module._mongo.setUp()
#    
#def tearDownModule(module):
#    module._appServerFixture.tearDown()
#    module._mongo.tearDown()
#    
#class RBACSystemJSONRPCTest(unittest.TestCase):
#    OK = 200
#    CREATED = 201
#    ACCEPTED = 202
#    BAD_REQUEST = 400
#    UNAUTHORIZED = 401
#    NOTFOUND = 404
#    GONE = 410
#    
#    def setUp(self):
#        self.http = httplib2.Http()
#        self.serviceURL = "http://localhost:8888/rbac_jsonrpc/"
#        self.memcached = RemoteMemStoreFixture()
#        self.memcached.setUp()
#        self._config = TestConfiguration.createInstance()
#        self._store = MongoStoreFactory.createInstance(self._config)        
#        self._creationAndAuthentication()       
#                 
#    def _creationAndAuthentication(self):
#        # Create Admin role
#        role1 = Role('AdminRole')
#        role1.isSuperAdmin = True 
#        self.role1ID = str(role1.save(self._store))
#        
#        # Create User role
#        role2 = Role('UserRole')
#        role2.isSuperAdmin = False 
#        self.role2ID = str(role2.save(self._store))
#        
#        # Create a role, win't be assigned to any user here
#        self.anyRoleID = str(Role('UserRole').save(self._store))
#        
#        # create ResourcePermissions
#        rp = ResourcePermission(RBACSystem.GET, RBACSystem.USER)
#        rp.roles = [self.anyRoleID]
#        rp.save(self._store)
#
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.USER)
#        rp.roles = [self.anyRoleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.ACTIVATE, RBACSystem.USER)
#        rp.roles = [self.anyRoleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.DELETE, RBACSystem.USER)
#        rp.roles = [self.anyRoleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.ROLE)
#        rp.roles = [self.anyRoleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.UPDATE, RBACSystem.ROLE)
#        rp.roles = [self.anyRoleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.DELETE, RBACSystem.ROLE)
#        rp.roles = [self.anyRoleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.ASSIGN, RBACSystem.USER)
#        rp.roles = [self.anyRoleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.UPDATE, RBACSystem.USER)
#        rp.roles = [self.anyRoleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.ASSIGN, RBACSystem.ROLE)
#        rp.roles = [self.anyRoleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.UPDATE, RBACSystem.PASSWORD)
#        rp.roles = [self.anyRoleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.ADD, RBACSystem.PERMISSION)
#        rp.roles = [self.anyRoleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.GET, RBACSystem.ROLE)
#        rp.roles = [self.anyRoleID]
#        rp.save(self._store)
#        
#        rp = ResourcePermission(RBACSystem.REVOKE, RBACSystem.PERMISSION)
#        rp.roles = [self.anyRoleID]
#        rp.save(self._store)
#        
#        #Create admin
#        user1 = AuthUser("admin", Crypto.encrypt(self._config, "root", self._config.main.default_crypto_algorithm), None)
#        user1.roleIDs = [self.role1ID]
#        user1.state = None
#        user1.save(self._store)
#        
#        #Create normal user
#        user2 = AuthUser("normalUser", Crypto.encrypt(self._config, "normalPass", self._config.main.default_crypto_algorithm), None)
#        user2.roleIDs = [self.role2ID]
#        user2.state = None
#        user2.save(self._store)
#        
#        #Authenticate Admin
#        url = self.serviceURL + "user/authenticate/admin/root"
#        self.guestHeader = {'HTTP_ACCEPT': 'json'}
#        (resp1, _) = self.http.request(url, 'GET', None, headers=self.guestHeader)
#        self.adminHeader = {'HTTP_ACCEPT': 'json', 'Cookie': resp1['set-cookie']}
#        
#        #Authenticate normal user
#        url = self.serviceURL + "user/authenticate/normalUser/normalPass"
#        (resp2, _) = self.http.request(url, 'GET', None, headers=self.guestHeader)
#        self.userHeader = {'HTTP_ACCEPT': 'json', 'Cookie': resp2['set-cookie']}
#            
#    def tearDown(self):            
#        for role in Role.find(self._store, Role(None)):
#            Role.remove(self._store, role)
#        
#        for rp in ResourcePermission.find(self._store, ResourcePermission(None, None)):
#            ResourcePermission.remove(self._store, rp)
#        
#        for user in AuthUser.find(self._store, AuthUser(None, None, None)):
#            AuthUser.remove(self._store, user)
#        
#        self.memcached.tearDown()
#        
#    def testAuthenticateLogout(self):
#        # Log in
#        url = self.serviceURL + "user/authenticate/admin/root"
#        (resp1, content1) = self.http.request(url, 'GET', None, headers=self.guestHeader)
#        self.assertTrue("c9.session_id" in resp1['set-cookie'])
#        self.assertEquals(self.OK, resp1.status)
#        ret1 = simplejson.loads(content1)
#        self.assertEquals(True, ret1)
#        
#        # Log out
#        url = self.serviceURL + "user/logout"
#        header = {'HTTP_ACCEPT': 'json', 'Cookie': resp1['set-cookie']}
#        (resp2, content2) = self.http.request(url, 'DELETE', None, headers=header)
#        self.assertTrue("c9.session_id" in resp2['set-cookie'])
#        self.assertEquals(self.OK, resp2.status) 
#        self.assertEquals(None, simplejson.loads(content2))
#        
#        # log in with bad password
#        url = self.serviceURL + "user/authenticate/admin/badPass"
#        (resp3, content3) = self.http.request(url, 'GET', None, headers=self.guestHeader)
#        self.assertTrue("c9.session_id" in resp3['set-cookie'])
#        self.assertEquals(self.OK, resp3.status)
#        ret3 = simplejson.loads(content3)
#        self.assertEquals(False, ret3)
#        
#        #Login with non-activated user
#        # Add new user ( as Guest )
#        body = '{"userID": "newUser", "password":"newPass"}'
#        (resp4, content4) = self.http.request(self.serviceURL + "user", 'POST', body, headers=self.guestHeader)
#        ret4 = simplejson.loads(content4)
#        self.assertEquals(self.CREATED, resp4.status)
#        self.assertTrue(isinstance(ret4, unicode))
#        # Login
#        url = self.serviceURL + "user/authenticate/newUser/newPass"
#        (resp5, content5) = self.http.request(url, 'GET', None, headers=self.guestHeader)
#        self.assertTrue("c9.session_id" in resp5['set-cookie'])
#        ret5 = simplejson.loads(content5)
#        self.assertEquals(self.OK, resp5.status)
#        self.assertEquals(False, ret5)
#        
#    def testUserAddDelete(self):
#        baseUrl = self.serviceURL + "user"
#        # Add existing user ( as Normal User )
#        body = '{"userID": "newUser", "password":"newPass"}'
#        (resp0, content0) = self.http.request(baseUrl, 'POST', body, headers=self.userHeader)
#        ret0 = simplejson.loads(content0)
#        self.assertEquals(self.UNAUTHORIZED, resp0.status)
#        self.assertEquals("user (normalUser) doesn't have enough permissions on (user)", ret0)
#        
#        # Add new user ( as Guest )
#        body = '{"userID": "newUser", "password":"newPass"}'
#        (resp1, content1) = self.http.request(baseUrl, 'POST', body, headers=self.guestHeader)
#        ret1 = simplejson.loads(content1)
#        self.assertEquals(self.CREATED, resp1.status)
#        self.assertTrue(isinstance(ret1, unicode))
#        
#        # Add existing user ( as Admin )
#        body = '{"userID": "newUser", "password":"newPass"}'
#        (resp2, content2) = self.http.request(baseUrl, 'POST', body, headers=self.adminHeader)
#        ret2 = simplejson.loads(content2)
#        self.assertEquals(self.BAD_REQUEST, resp2.status)
#        self.assertEquals("User with id (newUser) already exists!", ret2)
#        
#        # Add existing user ( as Normal User )
#        body = '{"userID": "newUser", "password":"newPass"}'
#        (resp3, content3) = self.http.request(baseUrl, 'POST', body, headers=self.userHeader)
#        ret3 = simplejson.loads(content3)
#        self.assertEquals(self.UNAUTHORIZED, resp3.status)
#        self.assertEquals("user (normalUser) doesn't have enough permissions on (user)", ret3)
#        
#        # Delete existing user ( as Guest )
#        url = baseUrl + "/newUser"
#        (resp0, content0) = self.http.request(url, 'DELETE', None, headers=self.guestHeader)
#        ret0 = simplejson.loads(content0)
#        self.assertEquals(self.UNAUTHORIZED, resp0.status)
#        self.assertEquals("user (Guest) doesn't have enough permissions on (user)", ret0)
#        
#        # Delete new user ( as Normal User )
#        (resp11, content11) = self.http.request(url, 'DELETE', None, headers=self.userHeader)
#        ret11 = simplejson.loads(content11)
#        self.assertEquals(self.UNAUTHORIZED, resp11.status)
#        self.assertEquals("user (normalUser) doesn't have enough permissions on (user)", ret11)
#        
#        # Delete existing user ( as Admin )
#        (resp21, content21) = self.http.request(url, 'DELETE', None, headers=self.adminHeader)
#        ret21 = simplejson.loads(content21)
#        self.assertEquals(self.OK, resp21.status) # OK
#        self.assertEquals(True, ret21)
#        
#        # Delete non-existing user ( as Admin )
#        (resp31, content31) = self.http.request(url, 'DELETE', None, headers=self.adminHeader)
#        ret31 = simplejson.loads(content31)
#        self.assertEquals(self.OK, resp31.status)
#        self.assertEquals(False, ret31)
#        
#    def testUserGetActivate(self):
#        baseUrl = self.serviceURL + "user"
#        # Add new user ( as Guest ), not activated
#        body = '{"userID": "newUser", "password":"newPass"}'
#        (resp1, content1) = self.http.request(baseUrl, 'POST', body, headers=self.guestHeader)
#        ret1 = simplejson.loads(content1)
#        self.assertEquals(self.CREATED, resp1.status)
#        self.assertTrue(isinstance(ret1, unicode))
#        
#        # Get that user, as Guest
#        url = baseUrl + "/newUser"
#        (resp2, content2) = self.http.request(url, 'GET', None, headers=self.guestHeader)
#        self.assertEquals(self.UNAUTHORIZED, resp2.status)
#        self.assertEquals("user (Guest) doesn't have enough permissions on (user)", simplejson.loads(content2))
#      
#        # Get that user, as normalUser
#        (resp3, content3) = self.http.request(url, 'GET', None, headers=self.userHeader)
#        self.assertEquals(self.UNAUTHORIZED, resp3.status)
#        self.assertEquals("user (normalUser) doesn't have enough permissions on (user)", simplejson.loads(content3))
#        
#        # Get that user, as Admin
#        (resp4, content4) = self.http.request(url, 'GET', None, headers=self.adminHeader)
#        user = simplejson.loads(content4)
#        self.assertEquals('newUser', user["userID"])
#        self.assertEquals(self.OK, resp4.status)
#        
#        # Activate the user, with bad token
#        body = '{"userID": "newUser", "activationToken":"badToken"}'
#        (resp5, content5) = self.http.request(baseUrl, 'PUT', body, headers=self.guestHeader)
#        ret5 = simplejson.loads(content5)
#        self.assertEquals(self.BAD_REQUEST, resp5.status)
#        
#        # Activate the user, without any token, as a Guest not admin
#        body = '{"userID": "newUser"}'
#        (resp6, content6) = self.http.request(baseUrl, 'PUT', body, headers=self.guestHeader)
#        self.assertEquals(self.BAD_REQUEST, resp6.status)
#        self.assertEquals("Activation Token is missing", simplejson.loads(content6))
#        
#        # Activate the user, with good token
#        body = '{"userID": "newUser", "activationToken":"' + ret1 + '"}'
#        (resp7, content7) = self.http.request(baseUrl, 'PUT', body, headers=self.guestHeader)
#        self.assertEquals(self.OK, resp7.status)
#        self.assertEquals(True, simplejson.loads(content7))
#        
#        # Activate already activated user
#        body = '{"userID": "newUser"}'
#        (resp8, content8) = self.http.request(baseUrl, 'PUT', body, headers=self.adminHeader) 
#        self.assertEquals(self.BAD_REQUEST, resp8.status)
#        
#        # Add another new user ( as Guest ), not activated
#        body = '{"userID": "anotherNewUser", "password":"anotherNewPass"}'
#        (resp1, content1) = self.http.request(baseUrl, 'POST', body, headers=self.guestHeader)
#        ret1 = simplejson.loads(content1)
#        self.assertEquals(self.CREATED, resp1.status)
#        self.assertTrue(isinstance(ret1, unicode))
#        # Activate anotherNewUser as admin
#        body = '{"userID": "anotherNewUser"}'
#        (resp10, content10) = self.http.request(baseUrl, 'PUT', body, headers=self.adminHeader)
#        self.assertEquals(self.OK, resp10.status)
#        self.assertEquals(True, simplejson.loads(content10))
#        
#    def testUserState(self):
#        baseURL = self.serviceURL + "user/state"
#        # getUserState
#        url = baseURL + "/normalUser"
#        (resp1, content1) = self.http.request(url, 'GET', None, headers=self.adminHeader)
#        ret1 = simplejson.loads(content1)
#        self.assertEquals(self.OK, resp1.status)
#        self.assertEquals(None, ret1) # user is None
#        
#        # getUserState, as normal User
#        url = baseURL + "/normalUser"
#        (resp2, content2) = self.http.request(url, 'GET', None, headers=self.userHeader)
#        ret2 = simplejson.loads(content2)
#        self.assertEquals(self.UNAUTHORIZED, resp2.status)
#        self.assertEquals("user (normalUser) doesn't have enough permissions on (user)", ret2)
#        
#        # getUserState, of non-existing user
#        url = baseURL + "/nonExistingUser"
#        (resp3, content3) = self.http.request(url, 'GET', None, headers=self.adminHeader)
#        ret3 = simplejson.loads(content3)
#        self.assertEquals(self.GONE, resp3.status)
#        self.assertEquals("User with id (nonExistingUser) does not have record in RBAC system!", ret3)
#        
#        # Test setUserState, to any random value
#        body = '{"userID":"nonExistingUser","state":"spam"}'
#        (resp4, content4) = self.http.request(baseURL, 'PUT', body, headers=self.adminHeader)
#        self.assertEquals(self.GONE, resp4.status)
#        self.assertEquals("User with id (nonExistingUser) does not have record in RBAC system!", simplejson.loads(content4))
#        
#        # Test setUserState to a random value
#        body = '{"userID":"normalUser","state":"nonValidState"}'
#        (resp5, content5) = self.http.request(baseURL, 'PUT', body, headers=self.adminHeader)
#        self.assertEquals(self.BAD_REQUEST, resp5.status)
#        
#        # Test setUserState, to a valid value
#        body = '{"userID":"normalUser","state":"spam"}'
#        (resp6, content6) = self.http.request(baseURL, 'PUT', body, headers=self.adminHeader)
#        self.assertEquals(self.OK, resp6.status)
#        self.assertEquals(True, simplejson.loads(content6))
#        
#    def testUserPassword(self):
#        baseURL = self.serviceURL + "user/password"
#        
#        # Test checkPassword    
#        url = baseURL + "/normalUser/ayPasswordWelSalam"
#        (_, content38) = self.http.request(url, 'GET', None, headers=self.guestHeader)
#        self.assertEquals(False, simplejson.loads(content38))
#        
#        # Test changePassword by oldPassword
#        body = '{"userID":"normalUser","newPassword":"ayPasswordWelSalam"}'
#        (resp39, content39) = self.http.request(baseURL, 'PUT', body, headers=self.adminHeader)
#        ret39 = simplejson.loads(content39)
#        self.assertEquals(self.OK, resp39.status)
#        self.assertEquals(True, ret39)
#        
#        # Test checkPassword
#        body = '{"userID":"normalUser", "password":"ayPasswordWelSalam"}'
#        (_, content40) = self.http.request(baseURL, 'GET', body, headers=self.guestHeader)
#        ret40 = simplejson.loads(content40)
#        self.assertEquals(True, ret40)
#        
#        # Test resetpassword 
#        url = baseURL + "/normalUser"
#        (resp41, content41) = self.http.request(url, 'DELETE', None, headers=self.guestHeader)
#        resetToken = simplejson.loads(content41)
#        self.assertEquals(200, resp41.status)
#        
#        # Test changePassword by reset key
#        body = '{"userID":"normalUser","newPassword":"theNewestPasswordHere", "resetKey":"' + resetToken + '"}'
#        (resp42, content42) = self.http.request(baseURL, 'PUT', body, headers=self.guestHeader)
#        ret42 = simplejson.loads(content42)
#        self.assertEquals(self.OK, resp42.status)
#        self.assertEquals(True, ret42)
#        
#        # Test checkPassword
#        body = '{"userID":"normalUser", "password":"theNewestPasswordHere"}'
#        (resp43, content43) = self.http.request(baseURL, 'GET', body, headers=self.guestHeader)
#        ret43 = simplejson.loads(content43)
#        self.assertEquals(self.OK, resp43.status)
#        self.assertEquals(True, ret43)
#    
#    def testPermissionsCheck(self):
#        baseURL = self.serviceURL + "permission/check"
#        # Test Check that admin has permission to add user
#        url = baseURL + "/admin/add/user"
#        (_, content14) = self.http.request(url, 'GET', None, headers=self.guestHeader)
#        ret14 = simplejson.loads(content14)
#        self.assertEquals(True, ret14)
#        
#        # Test Check that non-existing user  doesn't have permission to add user
#        url = baseURL + "/notEvenAUser/delete/user"
#        (resp15, content15) = self.http.request(url, 'GET', None, headers=self.guestHeader)
#        ret15 = simplejson.loads(content15)
#        self.assertEquals(self.NOTFOUND, resp15.status)
#        self.assertEquals("User with id (notEvenAUser) does not have record in RBAC system!", ret15)
#        
#        # Test Check that normalUser  doesn't have permission to add user
#        url = baseURL + "/normalUser/delete/user"
#        (resp16, content16) = self.http.request(url, 'GET', None, headers=self.guestHeader)
#        ret16 = simplejson.loads(content16)
#        self.assertEquals(self.OK, resp16.status)
#        self.assertEquals(False, ret16)
#        
#    def testPermissions(self):
#        baseURL = self.serviceURL + "permission"
#        # test Grant Permission to user as newUser
#        body = '{"roleID":"' + self.role2ID + '","permissionName":"get","resourceName":"user"}'
#        (resp26, content26) = self.http.request(baseURL, 'POST', body, headers=self.userHeader)
#        ret26 = simplejson.loads(content26)
#        self.assertEquals("user (normalUser) doesn't have enough permissions on (permission)", ret26)
#        self.assertEquals(self.UNAUTHORIZED, resp26.status)
#        
#        # test Grant Permission to user as Admin
#        body = '{"roleID":"' + self.role2ID + '","permissionName":"get","resourceName":"user"}'
#        (resp27, content27) = self.http.request(baseURL, 'POST', body, headers=self.adminHeader)
#        self.assertEquals(True, simplejson.loads(content27))
#        self.assertEquals(self.CREATED, resp27.status)
#        
#        # Test Check permission
#        #url = baseURL + "/check/normalUser/get/user"
#        body = '{"userID":"%s","permission":"%s","resource":"%s"}' % ("normalUser", "get", "user")
#        (resp1, content1) = self.http.request(baseURL + "/check", 'GET', body, headers=self.guestHeader)
#        self.assertEquals(True, simplejson.loads(content1))
#        self.assertEquals(self.OK, resp1.status)
#        
#        
#        # Test Check permission
#        url = baseURL + "/check/notAUser/get/user"
#        (resp2, content2) = self.http.request(url, 'GET', None, headers=self.guestHeader)
#        self.assertEquals("User with id (notAUser) does not have record in RBAC system!", simplejson.loads(content2))
#        self.assertEquals(self.NOTFOUND, resp2.status)
#        
#        
#        # test revokePermission to user as newUser
#        url = baseURL + "/" + self.role2ID + "/get/user"
#        (resp28, content28) = self.http.request(url, 'DELETE', None, headers=self.userHeader)
#        ret28 = simplejson.loads(content28)
#        self.assertEquals("user (normalUser) doesn't have enough permissions on (permission)", ret28)
#        self.assertEquals(self.UNAUTHORIZED, resp28.status)
#        
#        # test revokePermission to user as admin
#        url = baseURL + "/" + self.role2ID + "/get/user"
#        (resp29, content29) = self.http.request(url, 'DELETE', None, headers=self.adminHeader)
#        self.assertEquals(True, simplejson.loads(content29))
#        self.assertEquals(200, resp29.status)
#        
#        # test revokePermission to user as admin, again 
#        url = baseURL + "/" + self.role2ID + "/get/user"
#        (resp30, content30) = self.http.request(url, 'DELETE', None, headers=self.adminHeader)
#        self.assertEquals(False, simplejson.loads(content30))
#        self.assertEquals(200, resp30.status) # Even though permission was already deleted
#        
#    def testRole(self):
#        baseURL = self.serviceURL + "role"
#        
#        # Add Role, as user
#        body = '{"name":"myNewRole", "description":"Hello, Description"}'
#        (resp1, content1) = self.http.request(baseURL, 'POST', body, headers=self.userHeader)
#        self.assertEquals(self.UNAUTHORIZED, resp1.status)
#        self.assertEquals("user (normalUser) doesn't have enough permissions on (role)", simplejson.loads(content1))
#        
#        # Add Role, as admin
#        (resp2, content2) = self.http.request(baseURL, 'POST', body, headers=self.adminHeader)
#        self.assertEquals(self.CREATED, resp2.status)
#        myRoleID = simplejson.loads(content2)
#        self.assertTrue(isinstance(myRoleID, unicode))
#        
#        # Add existing Role, as admin
#        (resp3, content3) = self.http.request(baseURL, 'POST', body, headers=self.adminHeader)
#        self.assertEquals(self.BAD_REQUEST, resp3.status)
#        self.assertEquals("Role with Name (myNewRole) already exists!", simplejson.loads(content3))
#        
#        # update a role, as user
#        body = '{"id":"' + myRoleID + '", "newName":"myNewRole", "description":"Welcome new Description"}'
#        (resp3, content3) = self.http.request(baseURL, 'PUT', body, headers=self.userHeader)
#        self.assertEquals(self.UNAUTHORIZED, resp3.status)
#        self.assertEquals("user (normalUser) doesn't have enough permissions on (role)", simplejson.loads(content3))
#        
#        # update non-exisitng role a admin
#        body = '{"id":"notEvenAnID", "newName":"myNewRole", "description":"Welcome new Description"}'
#        (resp4, content4) = self.http.request(baseURL, 'PUT', body, headers=self.adminHeader)
#        self.assertEquals(self.GONE, resp4.status)
#        self.assertEquals("No role found with id notEvenAnID", simplejson.loads(content4))
#        
#        # update existing role a admin
#        body = '{"id":"' + myRoleID + '", "newName":"myNewRole", "description":"Welcome new Description"}'
#        (resp5, content5) = self.http.request(baseURL, 'PUT', body, headers=self.adminHeader)
#        self.assertEquals(self.OK, resp5.status)
#        self.assertEquals(True, simplejson.loads(content5))
#        
#        # delete the role        
#        url = baseURL + "/" + myRoleID
#        (resp6, content6) = self.http.request(url, 'DELETE', None, headers=self.adminHeader)
#        self.assertEquals(self.OK, resp6.status)
#        self.assertEquals(True, simplejson.loads(content6))
#        
#        # delete the role again
#        (resp7, content7) = self.http.request(url, 'DELETE', None, headers=self.adminHeader)
#        self.assertEquals(self.OK, resp7.status)
#        self.assertEquals(True, simplejson.loads(content7))
#        
#    def testUserRole(self):
#        baseURL = self.serviceURL + "user/role"
#        # Assign Role to user, as a normal User
#        body = '{"roleID":"' + self.anyRoleID + '","userID":"normalUser"}'
#        (resp1, content1) = self.http.request(baseURL, 'POST', body, headers=self.userHeader)
#        self.assertEquals("user (normalUser) doesn't have enough permissions on (role)", simplejson.loads(content1))
#        self.assertEquals(self.UNAUTHORIZED, resp1.status) # OPSS, Role doesn't exist !!
#        
#        # Assign Role to non exisitng user, as admin
#        body = '{"roleID":"' + self.anyRoleID + '","userID":"notUser"}'
#        (resp2, content2) = self.http.request(baseURL, 'POST', body, headers=self.adminHeader)
#        self.assertEquals("User with id (notUser) does not have record in RBAC system!", simplejson.loads(content2))
#        self.assertEquals(self.BAD_REQUEST, resp2.status)
#        
#        # Assign Role to existing user , as admin
#        body = '{"roleID":"' + self.anyRoleID + '","userID":"normalUser"}'
#        (resp3, content3) = self.http.request(baseURL, 'POST', body, headers=self.adminHeader)
#        self.assertEquals(None, simplejson.loads(content3))
#        self.assertEquals(self.CREATED, resp3.status)
#        
#        # Test unAssign Role from normalUser ( by himself )
#        url = baseURL + "/%s/%s" % ("normalUser", self.anyRoleID)
#        (resp32, content32) = self.http.request(url, 'DELETE', None, headers=self.userHeader)
#        self.assertEquals("user (normalUser) doesn't have enough permissions on (role)", simplejson.loads(content32))
#        self.assertEquals(self.UNAUTHORIZED, resp32.status)
#        
#        # Test unAssign admin Role from newUser ( by himself ) AGAIN , which should fail
#        url = baseURL + "/%s/%s" % ("newUser", self.anyRoleID)
#        (resp33, content33) = self.http.request(url, 'DELETE', None, headers=self.userHeader)
#        self.assertEquals(self.UNAUTHORIZED, resp33.status)
#        self.assertEquals("user (normalUser) doesn't have enough permissions on (role)", simplejson.loads(content33))
#        
#    def testGetRole(self):
#        baseURL = self.serviceURL + "role/"
#        # Get Role Users, as normalUser
#        url = baseURL + "users/" + self.role1ID
#        (resp1, content1) = self.http.request(url, 'GET', None, headers=self.userHeader)
#        self.assertEquals(self.UNAUTHORIZED, resp1.status)
#        self.assertEquals("user (normalUser) doesn't have enough permissions on (user)", simplejson.loads(content1))
#         
#        # Get Role Users, as admin
#        (resp2, content2) = self.http.request(url, 'GET', None, headers=self.adminHeader)
#        self.assertEquals(self.OK, resp2.status)
#        users = simplejson.loads(content2)
#        self.assertEquals(1, len(users))
#        self.assertTrue("admin" in users)
#        
#        # Get Role Users (but role has no users !), as admin
#        url = baseURL + "users/" + self.anyRoleID
#        (resp3, content3) = self.http.request(url, 'GET', None, headers=self.adminHeader)
#        self.assertEquals(self.OK, resp3.status)
#        self.assertEquals([], simplejson.loads(content3))
#        
#        # Get not existing Role Users, as admin
#        url = baseURL + "users/notARole"
#        (resp4, content4) = self.http.request(url, 'GET', None, headers=self.adminHeader)
#        self.assertEquals(self.NOTFOUND, resp4.status)
#        self.assertEquals("Role with id (notARole) does not exist!", simplejson.loads(content4))
#        
#        # Get Role by Name
#        url = baseURL + "AdminRole"
#        (resp5, content5) = self.http.request(url, 'GET', None, headers=self.adminHeader)
#        self.assertEquals(self.OK, resp5.status)
#        role = simplejson.loads(content5)
#        self.assertEquals(True, role["isSuperAdmin"])
#        
#        # Get Non existing Role by Name
#        url = baseURL + "notARole"
#        (resp6, content6) = self.http.request(url, 'GET', None, headers=self.adminHeader)
#        self.assertEquals(self.GONE, resp6.status)
