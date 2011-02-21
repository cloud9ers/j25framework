import unittest
import httplib2
from test.fixtures.AppServerFixture import AppServerFixture
import logging
from test.TestConfiguration import TestConfiguration
import j25
from test.fixtures.MongoDBFixture import MongoDBFixture
import simplejson
from urllib import urlencode

_appName = 'testapp'
_appServer = None
_store = None

def setUpModule(module):
    module._appServer = AppServerFixture()
    module._appServer.setUp()
    module._appServer.load_application('test.web.%s' % module._appName)
    j25._store = None
    module._mongo = MongoDBFixture()
    module._mongo.setUp()
    
def tearDownModule(module):
    module._appServer.tearDown()
    module._mongo.tearDown()
    j25._store = None
 
class WebOperations(unittest.TestCase):
    
    def setUp(self):
        global _appName
        self.http = httplib2.Http()
        self.config = TestConfiguration.create_instance()
        self.ip = self.config.main.ip
        self.port = self.config.main.port
        self.controller = 'MemberService'
        self.logger = logging.getLogger("WebOperations")

    def tearDown(self):
        pass

    def testBasicGet(self):
        action = 'basic'
        uri = 'http://%s:%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action)
        self.logger.info('Trying to access the URI : %s' % uri)
        response, content = self.http.request(uri, 'GET')
        self.assertEqual(200, response.status)
        self.assertEqual('text/plain', response['content-type'])        
        self.assertEqual('basic operation', content)
        
    def testMemberOperations(self):
        #test adding new member GET
        action = 'addMember'
        name = 'ahmed'
        password = 'redhat'
        uri = 'http://%s:%s/%s/%s/%s?name=%s&password=%s' % (self.ip, self.port, _appName, self.controller, action, name, password)
        self.logger.info('Trying to access the URI : %s ' % uri)
        response, content = self.http.request(uri, 'GET')
        self.assertEqual(200, response.status)
        self.assertEqual('text/plain', response['content-type'])
        id = content
        self.assertNotEqual(None, id)

        #test adding new member POST
        action = 'addMember'
        name = 'ihab'
        password = 'cloud9ers'
        body = {'name': name, 'password': password}
        body = urlencode(body)
        uri = 'http://%s:%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action)
        self.logger.info('Trying to access the URI : %s ' % uri)
        response, content = self.http.request(uri, 'POST', body=body)
        self.assertEqual(200, response.status)
        self.assertEqual('text/plain', response['content-type'])
        id = content
        self.assertNotEqual(None, id)

        #test requesting a dict, should send populated template instead
        action = 'getMember'
        uri = 'http://%s:%s/%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action, id)
        self.logger.info('Trying to access the URI : %s ' % uri)
        response, content = self.http.request(uri, 'GET')
        self.logger.info(content)
        self.assertEqual(200, response.status)
        self.assertEqual('text/html', response['content-type'])
        self.assertEqual('<html><head>Mermber Service</head><body>ID:%s-name:%s-password:%s</body></html>' % (id, name, password), content)

        #test requesting invalid url
        action = 'invalid-action'
        uri = 'http://%s:%s/%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action, name)
        self.logger.info('Trying to access the URI : %s ' % uri)
        response, content = self.http.request(uri, 'GET')
        self.assertEqual(404, response.status)
        self.assertEqual('text/plain', response['content-type'])
        self.assertNotEqual(None, content)

        #test requesting getMember.json GET
        action = 'getMember'
        uri = 'http://%s:%s/%s/%s/%s.json/%s' % (self.ip, self.port, _appName, self.controller, action, id)
        self.logger.info('Trying to access the URI : %s ' % uri)
        response, content = self.http.request(uri, 'GET')
        self.assertEqual(200, response.status)
        self.assertEqual('application/json', response['content-type'])
        memberJSON = simplejson.loads(content)
        self.assertEqual(id, memberJSON['_id'])
        self.assertEqual(name, memberJSON['name'])
        self.assertEqual(password, memberJSON['password'])
        
        #test requesting getMember.json PUT
        action = 'updateMember'
        name = 'mohammed'
        password = 'fedora'
        body = {'name': name, 'password': password}
        body = simplejson.dumps(body)
        uri = 'http://%s:%s/%s/%s/%s.json/%s' % (self.ip, self.port, _appName, self.controller, action, id)
        self.logger.info('Trying to access the URI : %s ' % uri)
        response, content = self.http.request(uri, 'PUT', body=body)
        self.assertEqual(200, response.status)
        self.assertEqual('application/json', response['content-type'])
        memberJSON = simplejson.loads(content)
        self.assertEqual(id, memberJSON['_id'])
        self.assertEqual(name, memberJSON['name'])
        self.assertEqual(password, memberJSON['password'])

        #test requesting a string value GET
        action = 'getMemberName'
        uri = 'http://%s:%s/%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action, id)
        self.logger.info('Trying to access the URI : %s ' % uri)
        response, content = self.http.request(uri, 'GET')
        self.assertEqual(200, response.status)
        self.assertEqual('text/plain', response['content-type'])
        memberName = content
        self.assertEqual(name, memberName)