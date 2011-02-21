from framework.model.Document import Document

class Role(Document):
    DEFAULT = "Guest"
    def __init__(self, roleName):
        self.roleName       = roleName      #    string role name        
        self.description    = None          #    string represent role description
        self.isSuperAdmin   = False         #    guru user
