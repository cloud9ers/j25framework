from test.web.testproject.apps.kalamna.model.User import User
from j25.web import Controller
import simplejson
from j25.utils.JSONCustomEncoder import JSONCustomEncoder
import json
from j25 import Http

class Controller1(Controller):

    def check_request(self):
        if self.request.method == "POST":
            return "post request"
        else:   
            return "get request"
    
    def add_user(self):
        if self.request.method == 'GET':
            name = self.request.GET['name']
            password = self.request.GET['password']
            age = self.request.GET['age']
        else:
            name = self.request.POST['name']
            password = self.request.POST['password']
            age = self.request.POST['age']
            
        user = User(name=name, password=password, age=age)
        id = user.save()
        return user.id
    
    def update_user(self, id):
        if self.request.method == 'GET':
            name = self.request.GET['name']
        else:
            name = self.request.POST['name']
        return User.objects(id=id).update_one(set__name=name)
    
    def get_user_by_id(self, id):
        return User.objects(id=id).first()

    def get_user_name(self, id):
        user = User.objects(id=id).first()
        return user.name
    
    def get_user_by_name(self, name):
        return User.objects(name=name).first()
    
    def get_users(self):
        return User.objects()
    
    def test_get(self):
        return Http.OK
    
    def test_post(self):
        return Http.ACCEPTED
    
    def test_format(self, format=None):
        import pdb;pdb.set_trace()
        if format == "json":
#            return "json"
            return {'format': format}
        else:
#            return "other"
            return {'format': 'other'}
   