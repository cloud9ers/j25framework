from j25.model import *

class Member(Document):
    def __init__(self, name, password):
        self.name = name
        self.password = password
        