from j25.web import Controller
import simplejson

class Controller1(Controller):
#    def basic(self):
#        return 'basic test'

    def getData(self):
        if self.request.method == "POST":
            return "post"
        else:   
            return "get"