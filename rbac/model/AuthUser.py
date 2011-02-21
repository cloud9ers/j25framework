from framework.model.Document import Document
import bisect

class AuthUser(Document):
    ''' 
        RBAC user data
    '''
    #states
    DISABLED = 0x1
    SUSPENDED = 0x2
    SPAM = 0x3
    NEW = 0x4
    _mapState = {
                 'disabled': DISABLED,
                 'suspended': SUSPENDED,
                 'spam': SPAM,
                 'new': NEW
                 }
    
    def __init__(self, userID, password, state):
        '''
            @param userId: a string representing the user id on the system
            @param password: a string representing the user password
            @param flags: a list representing the flags of the user, (currently, disabled & lost password)
        '''
        self.userID = userID
        self.password = password
        self.state = state
        '''roleIDs: a list of ids of roles granted to user'''
        self.roleIDs = []
        '''lastLoginDatetime: a string representing user's last login datetime'''
        self.lastLoginDatetime = None
        '''lastLoginIP:a string representing the last IP user was logged in from'''
        self.lastLoginIP = None
        self.tokens = []
        
    def assignRole(self, roleID):
        '''
            @return: void
        '''
        if not self.roleIDs:
            self.roleIDs = [roleID]
        else:
            i = bisect.bisect_left(self.roleIDs, roleID)
            if i != len(self.roleIDs) and self.roleIDs[i] == roleID:
                return False
            self.roleIDs.insert(i, roleID)           
        return True
            
    def unassignRole(self, roleID):
        '''
            @return: True if the role was unassigned correctly, False if the user didn't have that role originally
        '''
        if roleID in self.roleIDs:
            self.roleIDs.remove(roleID)
            return True
        return False
    
    def setState(self, stateString):
        '''
            @return: True if state is assigned correctly, False if not (i.e state string is invelid)
        '''
        if stateString is not None and stateString not in  self._mapState:
            return False
        self.state = self._mapState.get(stateString, None)
        return True
    
    def getState(self):
        '''
            @return: state as a string
        '''
        for k, v in self._mapState.iteritems():
            if v == self.state:
                return k