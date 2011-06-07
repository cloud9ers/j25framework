from test.fixtures.Fixture import Fixture
from test.TestConfiguration import TestConfiguration
import logging
from test.fixtures.AppServerFixture import AppServerFixture
from test.fixtures.MongoDBFixture import MongoDBFixture
from test.fixtures.RabbitMQFixture import RabbitMQFixture
from test.fixtures.RemoteMemStoreFixture import RemoteMemStoreFixture
from j25.exceptions.RunningInstanceExceptions import RunningInstanceExceptions

class AllFixtures(Fixture):
    _FIXTURES = {'names' : "AppServer, MongoDB, RabbitMQ, MemCached"}
    
    def __init__(self, config=None):
        self.config = config or TestConfiguration.create_instance()
        self.appServer = AppServerFixture(config=self.config)
        self.mongoDB = MongoDBFixture(config=self.config)
#        self.rabbitMQ = RabbitMQFixture(config=self.config)
        self.remoteMemStore = RemoteMemStoreFixture(config=self.config)
        
    def startUp(self):
        logging.info('STARTING UP (%(names)s) fixtures ...' %AllFixtures._FIXTURES)
        #starting the MongoDB server
        try:
            self.mongoDB.setUp()
        except RunningInstanceExceptions, e:
            raise e
        #starting the RabbitMQ server
#        try:
#            self.rabbitMQ.setUp()
#        except RunningInstanceExceptions, e:
#            logging.debug("stopping the started fixtures")
            self.mongoDB.tearDown()
            raise e
        #starting the RemoteMemStore server
        try:
            self.remoteMemStore.setUp()
        except RunningInstanceExceptions, e:
            logging.debug("stopping the started fixtures")
            self.mongoDB.tearDown()
#            self.rabbitMQ.tearDown()
            raise e
        #starting the application server
        self.appServer.setUp()

        logging.info('All fixtures (%(names)s) started up successfully' %AllFixtures._FIXTURES)
         
    def tearDown(self):
        logging.info('SUTTING DOWN (%(names)s) fixtures ...' %AllFixtures._FIXTURES)
        #shutting down the application server
        try:
            self.appServer.tearDown()
        except:
            logging.critical("Couldn't stop application server")
        #shutting down the RemoteMemStore server
        try:
            self.remoteMemStore.tearDown()
        except:
            logging.critical("Couldn't stop memcached")
        #shutting down the RabbitMQ server
#        try:
#            self.rabbitMQ.tearDown()
#        except:
#            logging.critical("Couldn't stop RABBITMQ")
        #shutting down the MongoDB server
        self.mongoDB.tearDown()
        logging.info('All fixtures (%(names)s) shut down successfully' %AllFixtures._FIXTURES)

