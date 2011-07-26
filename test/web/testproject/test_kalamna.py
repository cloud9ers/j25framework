from test.fixtures.AppServerFixture import AppServerFixture
from test.fixtures.MongoDBFixture import MongoDBFixture
import unittest
import httplib2
from test.TestConfiguration import TestConfiguration
import logging
import j25
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
from j25.scripts.Server import setupLogging

_appName = 'kalamna'
_appServer = None
_store = None

def setUpModule(module):
    module._mongo = MongoDBFixture()
    module._mongo.setUp()
    import test.web.testproject
    module._appServer = AppServerFixture(projectDir=test.web.testproject.__path__[0])
    module._appServer.setUp()
    module._dispatcher = SimpleXMLRPCDispatcher(allow_none=True, encoding="UTF-8")
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
        pass

    def testBasicGet(self):
        action = 'getData'
        uri = 'http://%s:%s/%s/%s/%s' % (self.ip, self.port, _appName, self.controller, action)
        self.logger.info('Trying to access the URI : %s' % uri)
        response, content = self.http.request(uri, 'GET')
        