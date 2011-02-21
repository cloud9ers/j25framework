from j25.Configuration import Configuration
from j25.exceptions.ConfigurationExceptions import ConfigurationException
        
class TestConfiguration(Configuration):

    def __init__(self):
        #private constructor, use the factories instead
        raise ConfigurationException
    
    @staticmethod
    def create_instance():       
        ##loading the Default configuration
        cfg = Configuration.create_instance()

        cfg.main.services_packages = "test.sample_services, test.sample_services2"
        cfg.main.model_packages = "test.dummy"        
        ##setting the Test-Mode custom configurations
        cfg.main.project_name = "Test Project"
        cfg.main.ip = "127.0.0.1"
        cfg.main.port = "8888"

        # Cache regions
        cfg.cache.regions = "mongodbCache, memcached"
        
        # configuration for mongodb cache region
        cfg.cache.mongodbCache_type = "mongodb"
        cfg.cache.mongodbCache_url = ("mongodb://localhost:27017/c9CachingDB#c9CachingCollection")
        cfg.cache.add_option("mongodbCache_expire", 604800)
        
        # configuration for mongodb memcached region
        cfg.cache.memcached_type = "ext:memcached"
        cfg.cache.memcached_url = "127.0.0.1:9090"
        cfg.cache.add_option("memcached_expire", 604800)

        # Setting the memcached testing server parameters
        cfg.memcached.servers = "127.0.0.1:9090"

#        # Setting Test-Exchange configuration
        testExchangeSection = cfg.add_section("messagebus_test_exchange")
        testExchangeSection.add_option('exchange_type', 'fanout') # default exchange type       
        return cfg