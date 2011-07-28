from test.fixtures.AppServerFixture import AppServerFixture
from test.fixtures.MongoDBFixture import MongoDBFixture
import unittest
import httplib2
from test.TestConfiguration import TestConfiguration
import logging
import j25
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
from j25.scripts.Server import setupLogging
import json
from test.web.testproject.apps.kalamna.model.User import User
from urllib import urlencode

_appName = 'kalamna'
_appServer = None
_store = None

def setUpModule(module):
    module._mongo = MongoDBFixture()
    module._mongo.setUp()
    import test.web.testproject
    module._appServer = AppServerFixture(projectDir=test.web.testproject.__path__[0])
    module._appServer.setUp()
    module._appServer.loadApplication('apps.%s' % module._appName)
    
    
def tearDownModule(module):
    module._appServer.tearDown()
    module._mongo.tearDown()
 
class WebOperations(unittest.TestCase):
    
    def setUp(self):
        global _appName
        self.http = httplib2.Http()
        self.config = TestConfiguration.create_instance()
        self.ip = self.config.main.ip
        self.port = self.config.main.port
        self.controller = 'Controller1'
        self.logger = logging.getLogger("WebOperations")

    def tearDown(self):
        User.drop_collection()

    def test_basic_request(self):
        action = 'check_request'
        uri = 'http://%s:%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action)
        self.logger.info('Trying to access the URI : %s' % uri)
        
        response, content = self.http.request(uri, 'GET')
        self.assertEqual(200, response.status)
        self.assertEqual('text/plain; charset=UTF-8', response['content-type'])
        self.assertEqual('get request', content)
        response, content = self.http.request(uri, 'POST')
        self.assertEqual(200, response.status)
        self.assertEqual('text/plain; charset=UTF-8', response['content-type'])
        self.assertEqual('post request', content)
    
    def test_db_operations(self):
        # adding user using get method
        action="add_user"
        name="medo"
        password="password"
        age=25
        uri = 'http://%s:%s/%s/%s/%s?name=%s&password=%s&age=%s' % (self.ip, self.port, _appName, self.controller, action, name, password, age)
        response, content = self.http.request(uri, 'GET')
        id=content
        self.assertEqual(200, response.status)
        
        ## adding user using post method
        data={'name':'hamdy', 'password':'fedora', 'age':27}
        data = urlencode(data)
        uri = 'http://%s:%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action)
        response, content = self.http.request(uri, 'POST', body=data)
        self.assertEqual(200, response.status)
        self.assertEqual(response['content-type'], 'text/plain; charset=UTF-8')
        
        action="get_user_by_id"
        uri = 'http://%s:%s/%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action, id)
        response, content = self.http.request(uri, 'GET')
        self.assertEqual(200, response.status)
        data = json.loads(content)
        self.assertEqual(data['name'], "medo")
        self.assertEqual(data['password'], "password")
        self.assertEqual(data['age'], 25)

        ## update user using get method
        action="update_user"
        name="ahmed"
        uri = 'http://%s:%s/%s/%s/%s/%s?name=%s' % (self.ip, self.port, _appName, self.controller, action, id, name)
        response, content = self.http.request(uri, 'GET')
        self.assertEqual(200, response.status)
        self.assertEqual(response['content-type'], 'text/plain; charset=UTF-8')
        self.assertEqual(content, '1')

        action="get_user_by_id"
        uri = 'http://%s:%s/%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action, id)
        response, content = self.http.request(uri, 'GET')
        self.assertEqual(200, response.status)
        data = json.loads(content)
        self.assertEqual(data['_id'], id)
        self.assertEqual(data['name'], "ahmed")

        ## update user using post method
        action="update_user"
        uri = 'http://%s:%s/%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action, id)
        data = {'name':"medo"}
        data = urlencode(data)
        response, content = self.http.request(uri, 'POST', body=data)
        self.assertEqual(200, response.status)
        self.assertEqual(response['content-type'], 'text/plain; charset=UTF-8')
        self.assertEqual(content, '1')
        
        ## test get user using post method
        action="get_user_by_id"
        uri = 'http://%s:%s/%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action, id)
        response, content = self.http.request(uri, 'POST')
        self.assertEqual(201, response.status)
        data = json.loads(content)
        self.assertEqual(data['_id'], id)
        self.assertEqual(data['name'], "medo")

        action="get_user_name"
        uri = 'http://%s:%s/%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action, id)
        response, content = self.http.request(uri, 'GET')
        self.assertEqual(200, response.status)
        self.assertEqual(content, "medo")
        
        action="get_user_by_name"
        name = "medo"
        uri = 'http://%s:%s/%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action, name)
        response, content = self.http.request(uri, 'GET')
        self.assertEqual(200, response.status)
        data = json.loads(content)   
        self.assertEqual(data['name'], "medo")
        self.assertEqual(data['_id'], id)
        
        action="get_users"
        uri = 'http://%s:%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action)
        response, content = self.http.request(uri, 'GET')
        self.assertEqual(200, response.status)  
        data = json.loads(content)
        self.assertEqual(2, len(data))
        self.assertTrue(isinstance(data, list))

        action="test"
        uri = 'http://%s:%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action)
        response, content = self.http.request(uri, 'GET')
        self.assertEqual(200, response.status)  
        self.assertEqual(0, len(content))
        
        action="test"
        uri = 'http://%s:%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action)
        response, content = self.http.request(uri, 'POST')
        self.assertEqual(202, response.status)  
        self.assertEqual(0, len(content))
        
#        action="test_format"
#        format = "json"
#        uri = 'http://%s:%s/%s/%s/%s.%s' % (self.ip, self.port, _appName, self.controller, action, format)        
#        response, content = self.http.request(uri, 'GET')
#        data = json.loads(content)
#        self.assertEqual(data['format'], 'json')
#        self.assertEqual(200, response.status)
        
#        format="xml"
#        uri = 'http://%s:%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action)        
#        response, content = self.http.request(uri, 'GET')
#        import pdb;pdb.set_trace()
#        data = json.loads(content)
#        self.assertEqual(data['format'], 'other')
#        self.assertEqual(200, response.status)        
        
        
        