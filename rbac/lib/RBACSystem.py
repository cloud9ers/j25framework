#import bisect
#from model.rbac.Role import Role
#from model.rbac.AuthUser import AuthUser
#from framework.security.Crypto import Crypto
#from model.rbac.AuthToken import AuthToken
#from model.rbac.ResourcePermission import ResourcePermission
#from framework.interfaces.DocumentStore import Query
#from framework.model.Document import Document
#from bson.errors import InvalidId
#import logging
#import datetime
#
#class AlreadyExistsException(Exception): pass
#class NotFoundException(Exception): pass
#class UnauthorizedException(Exception): pass
#
#class RBACSystem(object):
#    USER = "user"
#    ROLE = "role"
#    PERMISSION = "permission"
#    PASSWORD = "password"
#    ADD = "add"
#    ASSIGN = "assign"
#    GET = "get"
#    REVOKE = "revoke"
#    DELETE = "delete"
#    UNASSIGN = "unassign"
#    RESET = "reset"
#    ACTIVATE = "activate"
#    UPDATE = "update"
#        
#    def __init__(self, config, store, cache):
#        self._config = config
#        self._store = store
#        self._cache = cache
#
#    @staticmethod
#    def createInstance(config, store, cache):
#        return RBACSystem(config, store, cache)
#
#    def _checkSession(self, session, permission, resource):
#        ''' throws UnauthorizedException if session doesn't have permission
#            to do the required operation.
#        '''
#        userID = session and session.get('userID', None)
#        if not userID or not self.check(userID, permission, resource):
#            raise UnauthorizedException("user (%s) doesn't have enough permissions on (%s)"\
#                                         % (userID or "Guest", resource))
#        return True
#        
#    def _generateActivationToken(self, user):
#        '''@param user: AuthUser object.
#        ''' 
#        authToken = AuthToken.createInstance(AuthToken.ACTIVATE_ACCOUNT,
#                                         self._config.main.default_expire_days)
#        if not user.tokens:
#            user.tokens = []            
#        user.tokens.append(authToken)
#        return authToken.token
#    
#    def _removeActivationToken(self, user, token=None):
#        '''@param user: AuthUser object.
#           @param token: Authentication token: String.
#        '''
#        for i, token_ in enumerate(user.tokens or []):            
#            if token_.purpose == AuthToken.ACTIVATE_ACCOUNT:
#                if token and token_.token != token:
#                    return False
#                user.tokens.pop(i)
#                return True
#        return False
#                    
#    def _getRoleIfExists(self, id):
#        '''@return: Role object, if exists.
#           throws NotFoundException if not found or if id is invalid.
#        '''
#        try:
#            role = Role.findOne(self._store, self._store.createOID(id))
#            if role:
#                return role
#        except InvalidId, _:
#            logging.info("An attempt to retrieve a non-existent role with id (%s)", id)        
#        raise NotFoundException("Role with id (%s) does not exist!" % id)
#    
#    def _getUserIfExists(self, userID):
#        """@param userID: user id which is passed to AuthUser when creating user,
#                          not the Document id
#        """
#        user = AuthUser.findOne(self._store, AuthUser(userID, None, None)) if userID else None
#        if not user:
#            raise NotFoundException("User with id (%s) does not have record in RBAC system!" % userID)
#        return user
#    
#    def _getOrCreateGuestRoleOID(self):
#        ''' creates guest role if not created, return it if already created.
#            @return:OID of the Guest Role.
#         '''
#        role = Role.findOne(self._store, Role(Role.DEFAULT))
#        if not role:
#            role = Role(Role.DEFAULT)
#            role.description = "Guest role"
#            role.save(self._store)
#        return role.getOID()
#    
#    def _updateCachedPermissions(self, roleID, permission, resource, action):
#        '''
#            @param permission: permission name
#            @param resource: resource name
#            @param action: RBACSystem.ADD or RBACSystem.REVOKE
#        '''    
#        '''str(key) to avoid memcached unicode problem'''
#        key = str("%s|%s" % (permission, resource))
#        self._cache.createCollection(self._config.cache.cachedRolesCollection)        
#        try:
#            resourcePermissions = self._cache.get(self._config.cache.cachedRolesCollection, key).split(',')
#        except KeyError, _:
#            resourcePermissions = []    
#        i = bisect.bisect_left(resourcePermissions, roleID)               
#        if action == RBACSystem.REVOKE and not i == len(resourcePermissions):   
#            resourcePermissions.pop(i)
#            if not resourcePermissions:
#                self._cache.delete(self._config.cache.cachedRolesCollection, key)
#                return None                                  
#        if action == RBACSystem.ADD:
#            if not (i != len(resourcePermissions) and resourcePermissions[i] == roleID):
#                resourcePermissions.insert(i, roleID)
#        self._cache.set(self._config.cache.cachedRolesCollection, key, ','.join(resourcePermissions))
#                         
#    def _isSuperAdmin(self, session):
#        if session:
#            userID = session.get('userID', None)
#            roleIDs = AuthUser.findOne(self._store, AuthUser(userID, None, None)).roleIDs
#            for roleID in roleIDs:
#                if self._getRoleIfExists(roleID).isSuperAdmin:
#                    return True
#        return False
#        
#    
#    def addUser(self, userID, password, session):
#        ''' create user entry in RBAC System
#        @param userID: user id
#        @param password: user password
#        @param session: session object session (can be None)
#        @return (OID, ActivationKey)
#        '''   
#        session and self._checkSession(session, RBACSystem.ADD, RBACSystem.USER)
#        # check if no user exists with this ID
#        if AuthUser.findOne(self._store, AuthUser(userID, None, None)) :
#            raise AlreadyExistsException("User with id (%s) already exists!" % userID)
#        # add this user and generate activation token
#        user = AuthUser(userID,
#                            Crypto.encrypt(self._config, password, self._config.main.default_crypto_algorithm),
#                            AuthUser.NEW)
#        user.roleIDs = [str(self._getOrCreateGuestRoleOID())]
#        activationToken = self._generateActivationToken(user)
#        user.save(self._store, True)
#        return activationToken
#    
#    def deleteUser(self, userID, session):
#        ''' delete user entry from RBAC System
#        @param userId: a string representing the user id on the system
#        @param session: session object 
#        @return Boolean
#        '''
#        try:
#            self._checkSession(session, RBACSystem.DELETE, RBACSystem.USER)
#            user = self._getUserIfExists(userID)
#            AuthUser.remove(self._store, user)
#            return True
#        except NotFoundException, _:
#            return False
#    
#    def check(self, userID, permission, resource):
#        ''' check authorization for access for a given user on a given permission on a given resource
#        @param userID: a string representing user ID
#        @param permission: string
#        @param resource: string
#        @return: boolean
#        '''
#        self._cache.createCollection(self._config.cache.cachedRolesCollection)
#        user = self._getUserIfExists(userID)
#        if user.state: return False
#        
#        try:
#            roles = self._cache.get(self._config.cache.cachedRolesCollection, "%s|%s" % (permission, resource))
#            roles = roles.split(',')
#            roles = map(str, roles)
#        except KeyError:
#            resourcePermission = ResourcePermission.findOne(self._store, ResourcePermission(permission, resource))
#            if not resourcePermission: return False
#            roles = resourcePermission.getRoles()
#            self._cache.put(self._config.cache.cachedRolesCollection, str("%s|%s" % (permission, resource)), ','.join(roles))
#
#        for role in user.roleIDs:
#            if self._getRoleIfExists(role).isSuperAdmin: return True
#            i = bisect.bisect_left(roles, role)
#            if not i == len(roles) and roles[i] == role:
#                return True        
#        return False
#    
#    def getEffectivePermissions(self, userID):
#        ''' returns the effective permissions per user
#            @returns [(PERMISSION, RESOURCE),]
#        '''
#        user = self._getUserIfExists(userID)
#        roleIDs = user.roleIDs
#        effectivePermissions = []
#        for role in roleIDs:
#            rps = ResourcePermission.find(self._store, Document({'roles':role}))
#            for rp in rps:
#                effectivePermissions.append((rp.permission, rp.resource))
#        return effectivePermissions
#
#    def addRole(self, session, name, description=None):
#        ''' create new role
#        @param name: string
#        @param description: string
#        @param session: session object        
#        @return: roleID (OID)
#        '''
#        self._checkSession(session, RBACSystem.ADD, RBACSystem.ROLE)
#        role = Role(name)
#        if(Role.findOne(self._store, role)):
#            raise AlreadyExistsException("Role with Name (%s) already exists!" % name)
#        role.description = description
#        return role.save(self._store)
#    
#    def getRoleByName(self, name, session):
#        ''' returns the role object '''
#        self._checkSession(session, RBACSystem.GET, RBACSystem.ROLE)
#        role = Role(name)
#        role.isSuperAdmin = None
#        return Role.findOne(self._store, role)
#                    
#    def getAllRoles(self, session):
#        ''' returns a list of all roles
#            @param session: session object
#            @return: [(ID, Name),]
#        '''
#        self._checkSession(session, RBACSystem.GET, RBACSystem.ROLE)
#        roles = Role.find(self._store, Role(None))
#        if roles:
#            return [(str(role.getOID()), role.roleName) for role in roles]
#        return []
#
#    def updateRole (self, session, id, newName=None, description=None, isSuperAdmin=None):
#        ''' change the role of the given ID
#            @param id: a string representing the database document id
#            @param session: session object
#            @param newName: string
#            @param description: string
#            @param isSuperAdmin: boolean
#            @return: Boolean
#        '''
#        self._checkSession(session, RBACSystem.UPDATE, RBACSystem.ROLE)
#        try:
#            role = self._getRoleIfExists(self._store.createOID(id))
#            if newName:
#                role.roleName = newName
#            if description:
#                role.description = description
#            if not isSuperAdmin is None:
#                role.isSuperAdmin = isSuperAdmin
#            role.save(self._store)
#            return True
#        except NotFoundException, _:
#            return False
#        except InvalidId, _:
#            return False        
#
#    def renameRole(self, id, newName, session):
#        ''' change the name of a role given ID
#            @param id: a string representing the database document id
#            @param newName: string
#            @param session: session object
#            @return: Boolean
#        '''
#        self._checkSession(session, RBACSystem.UPDATE, RBACSystem.ROLE)
#        try:
#            role = self._getRoleIfExists(id)
#            role.roleName = newName
#            role.save(self._store)
#            return True
#        except NotFoundException, _:
#            return False        
#    
#    def updateRoleDescription(self, id, session, description=None):
#        ''' change the description of a role given ID
#            @param id: a string representing the database document id
#            @param description: string
#            @param session: session object
#            @return: Boolean
#        '''
#        self._checkSession(session, RBACSystem.UPDATE, RBACSystem.ROLE)
#        # check Role exists
#        try:
#            role = self._getRoleIfExists(id)
#            role.description = description
#            role.save(self._store)
#            return True
#        except NotFoundException, _:
#            return False
#    
#    def deleteRole(self, id, session):
#        ''' deletes an existing role
#            @param id: string 
#            @param session: session object
#            @return: None
#        '''
#        self._checkSession(session, RBACSystem.DELETE, RBACSystem.ROLE)
#        try:
#            oid = self._store.createOID(id)
#        except InvalidId, _:
#            return False
#        # Remove role from ResoucePermissions
#        resourcePermissions = ResourcePermission.find(self._store, Document({'roles':id}))
#        counter = len(resourcePermissions)
#        while (counter > 0):
#            rp = resourcePermissions.next() 
#            rp.roles.remove(id)
#            rp.save(self._store)
#            counter -= 1           
#            # update cache
#            self._updateCachedPermissions(id, rp.permission, rp.resource, RBACSystem.REVOKE)           
#
#        # Remove Role from users
#        users = AuthUser.find(self._store, Document({'roleIDs':id}))
#        counter = len(users)
#        while(counter > 0):
#            user = users.next()
#            user.unassignRole(id)
#            user.save(self._store)
#            counter -= 1
#            
#        Role.remove(self._store, oid)
#        return True
#    
#    def grantPermission(self, roleID, permissionName, resourceName, session):
#        ''' add access permission to role on resource
#            @param roleID: a string representing the database document id
#            @param permissionName: string
#            @param resourceName: string
#            @param session: session object
#            @return: None
#        '''
#        self._checkSession(session, RBACSystem.ADD, RBACSystem.PERMISSION)
#        resourcePermission = ResourcePermission.findOne(self._store, ResourcePermission(permissionName, resourceName))
#        if not resourcePermission:
#            resourcePermission = ResourcePermission(permissionName, resourceName)      
#        if resourcePermission.addRole(roleID):
#            resourcePermission.save(self._store)
#            self._updateCachedPermissions(roleID, permissionName, resourceName, RBACSystem.ADD)
#        return True
#            
#    def revokePermission(self, roleID, permissionName, resourceName, session):
#        ''' remove access permission on resource from role
#            @param roleId: a string representing the database document id
#            @param permissionName: string
#            @param resourceName: string
#            @param session: session object            
#            @return: None
#        '''
#        self._checkSession(session, RBACSystem.REVOKE, RBACSystem.PERMISSION)
#        resourcePermission = ResourcePermission.findOne(self._store, ResourcePermission(permissionName, resourceName))
#        if resourcePermission and roleID in resourcePermission.getRoles():
#                resourcePermission.roles.remove(roleID)
#                if not resourcePermission.roles:
#                    ResourcePermission.remove(self._store, resourcePermission, True)
#                else:
#                    resourcePermission.save(self._store)
#                self._updateCachedPermissions(roleID, permissionName, resourceName, RBACSystem.REVOKE)
#                return True
#        return False
#            
#    def getUsersByRole(self, roleID, session):
#        ''' returns a list of user ids in a given role
#            Throws NotFoundException, if roleID is invalid
#            @param roleID: a string representing the database document id
#            @return: list of users IDs
#        '''
#        self._checkSession(session, RBACSystem.GET, RBACSystem.USER)
#        # Check role if exists
#        self._getRoleIfExists(roleID)
#        query = AuthUser(None, None, None)
#        query.roleIDs = self._store.createQuery(Query.IS_IN, [roleID])
#        users = AuthUser.find(self._store, query)
#        if users:
#            return [user.userID for user in users]
#        return []
#    
#    def assignRoleToUser(self, userID, roleID, session):
#        ''' assign role to user
#            @param userID: string user id
#            @param roleID: OID
#            @param session: session object
#            @return None
#        '''
#        self._checkSession(session, RBACSystem.ASSIGN, RBACSystem.ROLE)
#        # Check role exists
#        self._getRoleIfExists(roleID)
#        # Check user exists
#        user = self._getUserIfExists(userID)
#        user.assignRole(roleID)
#        user.save(self._store)
#        
#    def unassignRoleFromUser(self, userID, roleID, session):
#        ''' unassign role from user
#            @param userID: string user id
#            @param roleID: string
#            @param session: session object
#            @return boolean
#        '''
#        self._checkSession(session, RBACSystem.UNASSIGN, RBACSystem.ROLE)
#        try:
#            # check role exists, and make sure roleID is valid
#            # Now NotFoundException is raised only if UserID not found
#            self._getRoleIfExists(roleID)
#        except NotFoundException, _:
#            return
#        # Remove role from user, or raise an exception if user is not in database
#        user = self._getUserIfExists(userID)
#        user.unassignRole(roleID)
#        user.save(self._store)
#
#    def getUser(self, userID, session):
#        ''' get user's full data
#            @param userId: a string representing the user id on the system
#            @param session: session object
#            @return session
#        '''
#        self._checkSession(session, RBACSystem.GET, RBACSystem.USER)
#        user = self._getUserIfExists(userID)
#        #remove password (encrypted but safety first)
#        del user.password
#        return user
#    
#    def setUserState(self, userID, state, session):
#
#        ''' check user state
#            @param userID: string user id
#            @param state: string with the new state
#            @param session: session object
#            @return boolean
#        '''
#        self._checkSession(session, RBACSystem.UPDATE, RBACSystem.USER)
#        user = self._getUserIfExists(userID)       
#        if user.setState(state):
#            user.save(self._store)
#            return True
#        return False
#    
#    def getUserState(self, userID, session):
#        ''' returns user current state 
#             @param userID: string user id
#             @param session: session object
#        '''
#        self._checkSession(session, RBACSystem.GET, RBACSystem.USER)
#        user = self._getUserIfExists(userID)
#        return user.getState()
#    
#    def changePassword(self, session, userID, newPassword, oldPassword=None, resetKey=None):
#        ''' change user password either using oldPassword OR using resetKey
#            @param userID: string user id
#            @param newPassword: string
#            @return boolean
#        '''
#        session and self._checkSession(session, RBACSystem.UPDATE, RBACSystem.PASSWORD)   
#        user = self._getUserIfExists(userID)
#        # If superAdmin bypass checks:
#        if not self._isSuperAdmin(session):
#            if not oldPassword and not resetKey: return False
#            if oldPassword and not self.checkPassword(userID, oldPassword): return False
#        
#            if resetKey:
#                today = datetime.datetime.now()
#                for index, token in enumerate(user.tokens or []):
#                    if token.purpose == AuthToken.RESET_PASSWORD and \
#                       token.token == resetKey and \
#                       token.expirationDatetime > today:
#                        user.tokens.pop(index)
#                        break
#                else:
#                    return False
#            
#        user.password = Crypto.encrypt(self._config, newPassword, self._config.main.default_crypto_algorithm)
#        user.save(self._store)
#        return True
#    
#    def resetUserPassword(self, userID, session=None):
#        '''
#            Returns reset key
#            @param userId: a string representing the user id on the system
#            @return reset_key
#        '''
#        session and self._checkSession(session, RBACSystem.RESET, RBACSystem.PASSWORD)        
#        user = self._getUserIfExists(userID)
#        token = AuthToken.createInstance(AuthToken.RESET_PASSWORD, self._config.main.default_expire_days)
#        if not user.tokens: user.tokens = []
#        user.tokens.append(token)
#        user.save(self._store)
#        return token.token
#    
#    def checkPassword(self, userID, password):
#        ''' checks the password ONLY, no state change
#            @param userId: a string representing the user id on the system
#            @param password: string
#            @return boolean
#        '''
#        encryptedPassword = Crypto.encrypt(self._config, password, self._config.main.default_crypto_algorithm)
#        user = AuthUser.findOne(self._store, AuthUser(userID, encryptedPassword, None)) # Add fields
#        if user:
#            return True
#        return False
#    
#    def authenticate(self, userID, password, session):
#        ''' password is hashed
#            @param userID: a string representing the user id on the system
#            @param password: string, hashed password
#            @return True or false
#        '''
#        if not self.checkPassword(userID, password): 
#            return False
#        user = self._getUserIfExists(userID)
#        if user.state: return False
#        # [ONHOLD] add lastLoginDatetime & lastLoginIP`
#        session.invalidate()
#        session['userID'] = userID
#        session['isLoggedIn'] = True
#        #session['currentLogin'] = datetime.datetime.now() #TODO
#        return True
#    
#    def activateUser(self, userID, session=None, activationToken=None):
#        ''' sets the state to None + removes activation token 
#            either give me session or activationToken to proceed.
#            Raises exception if both activationToken, and session are not given.
#        '''
#        if not session and not activationToken:
#            raise Exception("ActivationToken and session can't be both None")
#        
#        session and self._checkSession(session, RBACSystem.ACTIVATE, RBACSystem.USER)
#        user = self._getUserIfExists(userID)        
#        if self._removeActivationToken(user, activationToken):
#            user.setState(None)
#            user.save(self._store)
#            return True
#        return False
#            
#    def destroySession(self, session):
#        '''@param session: session object'''
#        session.invalidate()
