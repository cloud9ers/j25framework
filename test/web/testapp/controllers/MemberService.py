from j25.web import Controller
from test.web.testapp.model.Member import Member
import simplejson

class MemberService(Controller):
    def basic(self):
        return 'basic operation'
    
    def addMember(self):
        if self.request.method == 'GET':
            name = self.request.GET['name']
            password = self.request.GET['password']
        else:
            name = self.request.POST['name']
            password = self.request.POST['password']            
        member = Member(name, password)
        id = member.save()
        return id
    
    def getMember(self, id):
        member = Member.findOne(id)
        return member
    
    def getMemberName(self, id):
        member = Member.findOne(id)
        name = member.name
        return name
    
    def updateMember(self, id):
        parameters = simplejson.loads(self.request.body)
        member = Member.findOne(id)
        member.name = parameters['name']
        member.password = parameters['password']
        id = Member.save(member)
        member = Member.findOne(id)
        return member