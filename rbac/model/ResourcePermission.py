import bisect
from framework.model.Document import Document

class ResourcePermission(Document):
    def __init__(self, permission, resource):
        self.permission = permission
        self.resource = resource
        self.roles = [] #roleOIDs
        
    def addRole(self, roleID):
        if not self.roles:
            self.roles = [roleID]
        else:
            i = bisect.bisect_left(self.roles, roleID)
            if i != len(self.roles) and self.roles[i] == roleID:
                return False
            self.roles.insert(i, roleID)          
        return True
    
    def getRoles(self):
        return getattr(self, 'roles', [])
    