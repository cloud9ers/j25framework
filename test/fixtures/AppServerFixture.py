from j25.http.HttpServer import HttpServer
from j25.http.RequestDispatcher import RequestDispatcher
from j25.loaders.AppLoader import AutoAppLoader
from test.TestConfiguration import TestConfiguration
from test.fixtures.Fixture import Fixture
import j25
import logging
import threading
import time
from j25.scripts.Server import setupLogging
import sys

class AppServerFixture(Fixture):
    
    def __init__(self, config=None, projectDir=None):
        sys.path.insert(0, projectDir)
        self.config = config or TestConfiguration.create_instance()
        j25.config = self.config

    def loadApplication(self, application):
        self.appploader.load_application(application, j25._dispatcher)
            
    def setUp(self):
        setupLogging(logging.INFO)
        logger = logging.getLogger("j25")
        #setting configuration global
        j25.config = self.config
        
        #init store
        logger.debug("Connecting to Database")
        j25.initStore()
            
        #create the dispatcher
        self.appploader = AutoAppLoader([])
        j25._dispatcher = RequestDispatcher(self.appploader)
        j25._create_routing_middleware()
        j25._dispatcher.load_applications()
        #run the server and loop forever
        
        logging.info('STARTING the Application server')
        logger.info("\033[1;33mProject: %s\033[0m", self.config.main.project_name)
        self.ws = HttpServer(self.config)
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

