from framework.model.Document import Document
import uuid, datetime

class AuthToken(Document):
    #purposes
    RESET_PASSWORD = 0x4
    ACTIVATE_ACCOUNT = 0x5
    
    def __init__(self, token, purpose):
        self.token = token
        self.purpose = purpose #the purpose of the token
        self.generationDatetime = None
        self.expirationDatetime = None
        
    @staticmethod
    def createInstance(purpose, expireInDays):
        token = AuthToken(uuid.uuid4().hex, purpose)
        token.generationDatetime = datetime.datetime.now() 
        token.expirationDatetime = token.generationDatetime + datetime.timedelta(days=expireInDays)
        return token