from j25.interfaces.utils import interface
from hashlib import md5
class CryptoAlgorithm(object):
    def __init__(self):
        interface()
    def encrypt(self, data):
        interface()

class MD5CryptoAlgorithm(CryptoAlgorithm):
    def __init__(self):
        pass
        
    def encrypt(self, data):
        return md5(data).hexdigest()
            
class Crypto(object):
    MD5 = 'md5'
    _ALGORITHM_FACTORIES = {MD5: MD5CryptoAlgorithm}

    @staticmethod
    def encrypt(data, algorithm):
        algorithmInstance = Crypto._ALGORITHM_FACTORIES[algorithm]()
        return "%s/%s" % (algorithm, algorithmInstance.encrypt(data))