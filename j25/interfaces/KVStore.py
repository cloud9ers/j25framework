from j25.interfaces.utils import interface

class KVStore(object):
           
    @staticmethod
    def createInstance(config, collection):
        interface()
        
    def put(self, key, value):
        interface()
    
    def get(self, key):
        interface()
   
    def delete(self, key):
        interface()
    
    def flush(self):
        interface()
    
    def close(self):
        interface()
    
    def iteritems(self):
        interface()