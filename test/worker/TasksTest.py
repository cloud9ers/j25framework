#import unittest, time
#from test.fixtures.WorkerFixture import WorkerFixture
#from test.fixtures.RabbitMQFixture import RabbitMQFixture
#from test.tasks import Mathematician
#from test.fixtures.MongoDBFixture import MongoDBFixture
#
#_queue = None
#_worker = None
#
#def setUpModule(module):
#    module._queue = RabbitMQFixture()
#    module._worker = WorkerFixture()
#    module._queue.setUp()
#    module._worker.setUp()
#    
#def tearDownModule(module):
#    module._worker.tearDown()
#    module._queue.tearDown()
#
#class TasksTest(unittest.TestCase):
#    def setUp(self):
#        pass
#        
#    def tearDown(self):
#        time.sleep(2)
#        
#    def testModelAccess(self):
#        self.assertEquals(Mathematician.add.delay(10, 15).get(), 25)
#        self.assertEquals(Mathematician.playWithModel.delay().get(), 1)
#        d = Mathematician.getModelObj.delay(55).get()
#        self.assertTrue(d is not None)
#        self.assertEquals(d['id'], 55)
#    
#    def testExceptionMarshalling(self):
#        self.assertRaises(Exception, Mathematician.kaboom.delay().get)
#        
#    