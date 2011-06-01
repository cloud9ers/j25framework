from j25 import Constants
from j25.exceptions.StoreExceptions import UnknownStoreException
import logging

class MongoEngineFactory(object):
    logger = logging.getLogger("MongoEngineFactory")
    @staticmethod
    def create_instance(config):
        import mongoengine
        params = {}
        if config.store.ip:
            params['host'] = config.store.ip
        if config.store.port:
            params['port'] = int(config.store.port)
        if config.store.username:
            params['username'] = config.store.username
        if config.store.password:
            params['password'] = config.store.password
        MongoEngineFactory.logger.debug("Database name: %s", config.store.db_name)
        MongoEngineFactory.logger.debug("params: %s", params)
        try:
            db = mongoengine.connect(config.store.db_name, **params)
        except mongoengine.connection.ConnectionError, e:
            logging.critical("COULD NOT CONNECT TO MONGODB: %s", str(e))
            logging.critical("ALL DATABASE OPERATIONS WILL == FAIL ==")
            db = None
        MongoEngineFactory.logger.info("Connected to MongoDB:%s", config.store.db_name)
        return db

class StoreFactory(object):
    # Mappings of store types to factories
    _storesCreators =  {Constants.MONGOENGINE: MongoEngineFactory.create_instance}
    @staticmethod
    def create_instance(config):
        try:
            return StoreFactory._storesCreators[config.main.store_type](config)
        except KeyError, _:
            raise UnknownStoreException("Couldn't create a store instance of type: %s (Unknown Type)" % config.main.store_type)