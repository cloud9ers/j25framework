import unittest
from test.fixtures.AllFixtures import AllFixtures

_allFixtures = None

def setUpModule(module):
    module._allFixtures = AllFixtures()
    module._allFixtures.startUp()
    
def tearDownModule(module):
    module._allFixtures.tearDown()

class AllFixturesTest(unittest.TestCase):
      
    def setUp(self):
        pass
        
    def test(self):
        pass
    
    def tearDown(self):
        pass
            
   
