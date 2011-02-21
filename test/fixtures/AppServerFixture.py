from j25.http.HttpServer import HttpServer
from j25.http.RequestDispatcher import RequestDispatcher
from j25.loaders.AppLoader import AutoAppLoader
from test.TestConfiguration import TestConfiguration
from test.fixtures.Fixture import Fixture
import j25
import logging
import threading
import time

class AppServerFixture(Fixture):
    
    def __init__(self, config=None, servicesPackages=None, modelPackages=None):
        self.config = config or TestConfiguration.create_instance()
        j25.config = self.config
        self.modelPackages = modelPackages
        self.servicesPackages = servicesPackages

    def loadApplication(self, application):
        self.appploader.loadApplication(application, self.dispatcher, True)
            
    def setUp(self):
        self.appploader = AutoAppLoader([])
        self.dispatcher = RequestDispatcher(self.appploader)
        logging.info('STARTING the Application server')
        self.ws = HttpServer(self.dispatcher, self.config)
        self.thread = threading.Thread(target=self.ws.start)
        self.thread.start()
        while (not self.ws.is_running()):
            time.sleep(0.01)
         
    def tearDown(self):
        logging.info('STOPING the Application server')
        self.ws.stop()
        logging.info("Waiting for Application Server to terminate...")
        self.thread.join(60)
        logging.info("Application Server terminated")
        self.dispatcher = None

