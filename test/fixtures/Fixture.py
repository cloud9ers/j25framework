from j25.interfaces.utils import interface
import nose

class Fixture(nose.case.Test):    
    def setUp(self):
        interface()
        
    def tearDown(self):
        interface()