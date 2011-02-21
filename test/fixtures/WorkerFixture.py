from test.fixtures.Fixture import Fixture
from test.TestConfiguration import TestConfiguration
import subprocess, time
import os

class WorkerFixture(Fixture):
    def __init__(self, config=None):
        self.config = config or TestConfiguration.create_instance()
        
        
    def setUp(self):
        env = os.environ.copy()
        env['CELERY_LOADER'] = 'j25.worker.WorkerLoader.WorkerLoader'
        env['WORKER_CONFIG'] = 'test.fixtures.workerconfig'
        self.p = subprocess.Popen(['python', 'worker.py', '-l', 'INFO'], env=env, cwd="..")
        time.sleep(2)

    def tearDown(self):
        self.p.terminate()
        self.p.wait()
