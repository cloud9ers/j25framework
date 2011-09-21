import os
import logging, time
import subprocess
import tempfile
from test.fixtures.Fixture import Fixture
from test.TestConfiguration import TestConfiguration
from j25.exceptions.RunningInstanceExceptions import RunningInstanceExceptions
import psutil

class RabbitMQFixture(Fixture):
    def __init__(self, config=None):
        self.config = config or TestConfiguration.create_instance()
        self._rabbitDBBin = os.path.sep.join(['/usr', 'sbin', 'rabbitmq-server'])
        self._mnesia_base =  os.path.sep.join([tempfile.gettempdir(), 'mnesia'])
        
    def setUp(self):
        logging.info("Starting Up The Rabbit...")
        #Checking if the RabbitMQ service is already running
#        rabbitMQDeamon = 'beam.smp'
#        cmd = 'pidof '+ rabbitMQDeamon
#        p = os.popen(cmd)
#        o = p.readline()
#        o = [] if not o else map(lambda x: int(x.strip()), o.split(' '))
#        if(len(o) > 0):
#            raise RunningInstanceExceptions("Can not start RabbitMQ server as there are other RabbitMQ instances running  with PIDs :%s" %str(o))
        try:
            os.mkdir(self._mnesia_base)
        except:
            subprocess.call(['rm', '-rf', self._mnesia_base])
            os.mkdir(self._mnesia_base)
        os.environ['RABBITMQ_MNESIA_BASE'] = self._mnesia_base
        os.environ['RABBITMQ_LOG_BASE'] = self._mnesia_base
        
        if not os.path.isfile(self._rabbitDBBin):
            logging.critical("No rabbitmq daemon was found in %s", self._rabbitDBBin)
            raise Exception("RabbitMQ was not found in %s" % self._rabbitDBBin)
        logging.debug("Using RabbitMQ Installation in %s", self._rabbitDBBin)
        logging.info("RabbitMQ Instance running on mnesia path %s", self._mnesia_base)
        self.p = subprocess.Popen([self._rabbitDBBin])
        logging.info("Waiting for 5 seconds of second to let RabbitMQ settle")
        time.sleep(5)
        
    def tearDown(self):
        logging.info("Shutting Down RabbitMQ...!!")
        parent_process = psutil.Process(self.p.pid)
        for process in parent_process.get_children():
            process.kill()
            logging.info("process %s was killed", process.pid)
            time.sleep(0.2)
        self.p.terminate()
        self.p.wait()
        time.sleep(1.5)
        try:
            self.p.kill()
        except:
            pass
        try:
            subprocess.call(['rm', '-rf', self._mnesia_base])
        except OSError, e:
            logging.warn("couldn't be sure of removing RabbitMQ files: %s", str(e))