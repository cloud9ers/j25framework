''' should test HTTP server functionality '''
import unittest
from j25.http.HttpServer import HttpServer
from test.TestConfiguration import TestConfiguration
import socket
from j25.http.RequestDispatcher import RequestDispatcher
import time
import threading
from j25.loaders.AppLoader import AutoAppLoader

def setUpModule(module):
    pass
    
def tearDownModule(module):
    pass
    
class HttpServerTest(unittest.TestCase):
    def startUp(self):
        pass
    def tearDown(self):
        pass
    
    def testRestartability(self):
        ws = HttpServer(TestConfiguration.create_instance())
        self.assertFalse(self._isPortReserved(8888))
        thread = threading.Thread(target=ws.start)
        thread.start()
        while (not ws.is_running()):
            time.sleep(0.01)
        self.assertTrue(self._isPortReserved(8888))
        ws.stop()
        thread.join(10)
        self.assertFalse(self._isPortReserved(8888))
        
    def _isPortReserved(self, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", 8888))
            s.listen(10)
            s.close()
            return False
        except:
            return True
        finally:
            try:
                s.close()
            except:
                pass
        