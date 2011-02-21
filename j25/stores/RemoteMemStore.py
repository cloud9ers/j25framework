import memcache
import logging

from j25.interfaces.KVStore import KVStore

class RemoteMemStore(KVStore):  
    
    @staticmethod
    def create_instance(config, collection):
        return RemoteMemStore(config, collection)
           
    def __init__(self, config, collection):
        memcachedServers = [] if config.memcached.servers is None else map(lambda x: x.strip(), config.memcached.servers.split(','))
        logging.debug("Initializing %s: object, with servers %s", self, ''.join(memcachedServers))
        self._backend = memcache.Client(memcachedServers)
        self._config = config
        self._collection = collection

    def put(self, key, value, time=None, autoUpdateValue=False):
        """
            Adds a record to memcached server(s).
        """
        prefixed_key = "%s$%s" % (self._collection, key)
        time = self._config.memcached.expireTime if time is None else time
        result = self._backend.add(prefixed_key,
                              value,
                              time=time,
                              min_compress_len=self._config.memcached.min_compress_len)
        if not result:
            val_ = self.get(key)
            if  val_ and not autoUpdateValue:
                raise KeyError("key (%s) already exists" % key)
            else:                
                result = self._backend.set(prefixed_key,
                              value,
                              time=time,
                              min_compress_len=self._config.memcached.min_compress_len)  
        return result

    def get(self, key):
        """
            Returns the value assigned to a key, None if key not found.          
        """
        value = self._backend.get("%s$%s" % (self._collection, str(key)))
        if not value:
            logging.info("An attempt to get a non-existing key: %s from cache collection: %s@%s", key, self._collection, self)
            raise KeyError()
        return value

    def delete(self, key):
        """
            Deletes a record.
        """
        self._backend.delete("%s$%s" % (self._collection, key))      

    def close(self):
        self._backend.disconnect_all()
        self._backend = None
        self._config = None
        self._collection = None