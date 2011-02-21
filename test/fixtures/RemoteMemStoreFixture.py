import logging, time
import subprocess
import os
from test.fixtures.Fixture import Fixture
from test.TestConfiguration import TestConfiguration

class RemoteMemStoreFixture(Fixture):
    def __init__(self, config=None):
        self.config = config or TestConfiguration.create_instance()
        self._memCachedIn = os.path.sep.join([os.environ.get("MEMCACHED_HOME", "/usr/local"), 'bin', 'memcached'])
        
    def setUp(self):
        logging.info("Starting Up The MemCached...")
#        memcachedProcess = 'memcached'
#        cmd = 'pidof '+ memcachedProcess
#        p = os.popen(cmd)
#        o = p.readline()
#        o = [] if not o else map(lambda x: int(x.strip()), o.split(' '))
#        if(len(o) > 0):
#            raise RunningInstanceExceptions("Can not start MemCached server as there are other MemCached instances running  with PIDs :%s" %str(o))
        memcachedServers = [] if self.config.memcached.servers is None else map(lambda x: x.strip(), self.config.memcached.servers.split(','))
        if not os.path.isfile(self._memCachedIn):
            logging.critical("No memcached daemon was found in %s", self._memCachedIn)
            raise Exception("memcached was not found in %s" % self._memCachedIn)
        logging.debug("Using memcached Installation in %s", self._memCachedIn)
        self.p = subprocess.Popen([self._memCachedIn, '-p %s' % memcachedServers[0].split(':')[1]])
        logging.info("Memcached test process %s is running", self.p.pid)
        # Sleep for 0.2 seconds to make sure that memcached is running
        time.sleep(0.2)
        
    def tearDown(self):
        self.p.terminate()
        self.p.wait()
        time.sleep(1)
        logging.info("Memcached terminated")