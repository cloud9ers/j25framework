import logging
from j25.interfaces.KVStore import KVStore

class LocalMemStore(KVStore):
    @staticmethod
    def createInstance(config, collection):
        return LocalMemStore(collection)
    
    def __init__(self, collection):
        self._db = {}
        self._collection = collection

    def put(self, key, value, time=None, autoUpdateValue=False):
        """
            Puts a new record into an in-memory collection(Dictionary) inside a given LocalMemStore cache object.
        """
        logging.debug("Attempting to put key/value: %s/%s into an in-memory cache collection %s", key, value, self._collection)
        oldValue = self._db.get(key)
        if oldValue and not autoUpdateValue:
            raise KeyError("Attempting to add a duplicated key: %s into an in-memory cache collection %s" %(key, self._collection))         
        else:
            self._db[key] = value
        return value

    def get(self, key):
        """
            Returns the value assigned to a given key, None if key not found.
        """
        try:
            return self._db[key]
        except KeyError, _:
            logging.debug("An attempt to get a non existing key from an in-memory cache collection %s", self._collection)
            raise

    def keys(self, prefix=None, max=-1):
        """
            Returns a list of all/some keys.
        """
        prefix = prefix or ''
        preparedKeys = []
        for k in self._db:
            if len(preparedKeys) < max or max < 0:
                if k.startswith(prefix):
                    preparedKeys.append(k)
        return preparedKeys

    def delete(self, key):
        """
            Deletes a key
        """
        for key in self._db:
            return self._db.pop(key)
        raise KeyError('Cannot find key %s' % key)

    def flush(self, collection=None):
        """
            Expires all data in the in-memory collection.
        """
        self._db = None

    def close(self):
        self.flush()

    def iteritems(self):
        return self._db.iteritems()