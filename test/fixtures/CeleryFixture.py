import os
import logging, time
import subprocess
from test.fixtures.Fixture import Fixture

class CeleryFixture(Fixture):
    def __init__(self):
        self.celerybin =  os.path.sep.join(['/usr', 'local', 'bin', 'celeryd'])
        
    def setUp(self):
        logging.info("Starting Up Celery...")
        env = os.environ.copy()
        self.p = subprocess.Popen([self.celerybin])
        sleepTime = 2
        logging.info("Waiting for %s seconds of second to let celery settle" % sleepTime)
        time.sleep(sleepTime)
        
    def tearDown(self):
        logging.info("Shutting Down Celery...!!")
        self.p.terminate()
        time.sleep(1)
        self.p.kill()
        self.p.wait()
        time.sleep(1)