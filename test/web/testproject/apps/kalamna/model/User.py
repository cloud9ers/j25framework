from mongoengine import *
class User(Document):
#    def __init__(self, name, password, age):
#        self.name = name
#        self.password = password
#        self.age = age
    name = StringField()
    password = StringField()
    age = IntField()