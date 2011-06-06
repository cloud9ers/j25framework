import os
import logging, time
import subprocess
import tempfile
from test.fixtures.Fixture import Fixture
from test.TestConfiguration import TestConfiguration
#from j25.exceptions.RunningInstanceExceptions import RunningInstanceExceptions

class MongoDBFixture(Fixture):
    def __init__(self, config=None):
        self.config = config or TestConfiguration.create_instance()
        self._mongoDBBin = os.path.sep.join([os.environ.get("MONGODB_HOME", "/usr"), 'bin', 'mongod'])
        self._mongoDB =  os.path.sep.join([tempfile.gettempdir(), 'mongodb'])
        
    def setUp(self):
        logging.info("Starting Up MongoDB...")
        #Checking if the MongoDB service is already running
#        mongoDBProcess = 'mongod'
#        cmd = 'pidof '+ mongoDBProcess
#        p = os.popen(cmd)
#        o = p.readline()
#        o = [] if not o else map(lambda x: int(x.strip()), o.split(' '))
#        if(len(o) > 0):
#            raise RunningInstanceExceptions("Can not start MongoDB server as there are other MongoDB instances running with PIDs :%s" %str(o))
        try:
            os.mkdir(self._mongoDB)
        except:
            subprocess.call(['rm', '-rf', self._mongoDB])
            os.mkdir(self._mongoDB)
            
        if not os.path.isfile(self._mongoDBBin):
            logging.critical("No mongo daemon was found in %s", self._mongoDBBin)
            raise Exception("MongoDB was not found in %s" % self._mongoDBBin)
        logging.debug("Using MongoDB Installation in %s", self._mongoDBBin)
        logging.info("MongoDB Instance running on dbpath %s", self._mongoDB)
        self.p = subprocess.Popen([self._mongoDBBin, '--noprealloc', '--dbpath', self._mongoDB])
        logging.info("Waiting for a couple of second to let mongo settle")
        time.sleep(0.7)
        
    def tearDown(self):
        logging.info("Shutting Down MongoDB...")
        self.p.terminate()
        self.p.wait()
        time.sleep(0.8)
        try:
            subprocess.call(['rm', '-rf', self._mongoDB])
        except OSError, e:
            logging.warn("couldn't be sure of removing mongo files: %s", str(e))