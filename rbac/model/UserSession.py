from framework.model.Document import Document
import uuid
import datetime

class UserSession(Document):
    def __init__(self):
        pass
    
    @staticmethod
    def createInstance(userID):
        session = UserSession()
        session.id = uuid.uuid4().hex
        session.creationDatetime = datetime.datetime.now()
        session.userID = userID
        return session
    
    def __str__(self):
        return self.id
        