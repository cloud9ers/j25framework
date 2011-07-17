import ConfigParser
import os
import logging
from j25 import Constants
from j25.exceptions.ConfigurationExceptions import ConfigurationException
from j25.security.Crypto import Crypto

class Configuration(object):
    ''' Configuration Container
    NOTE: All attributes will be read as small even if they were wrote in capital in the file
    '''
    def __init__(self):
        #private constructor, use the factories instead
        raise ConfigurationException

    def add_section(self, sectionName):
        cfgObj = Configuration.__new__(Configuration)
        setattr(self, sectionName, cfgObj)
        return cfgObj

    def add_option(self, name, value):
        setattr(self, name, value)

    def has_option(self, name):
        return hasattr(self, name)

    def has_section(self, sectionName):
        return hasattr(self, sectionName)

    def get_section(self, sectionName):
        return getattr(self, sectionName)

    def get_option(self, optionName):
        return getattr(self, optionName)

    def options(self):
        return [o for o in dir(self) if not o.startswith('__') and \
                                        not callable(getattr(self, o))]

    def sections(self):
        return [s for s in dir(self) if not s.startswith('__') and \
                                        not callable(getattr(self, s))]

    @staticmethod
    def get_modules(configKey):
        return map(lambda x: __import__(x.strip(), fromlist='t'), filter(lambda x: len(x.strip()) > 0, configKey.split(',')))

    @staticmethod
    def create_empty_config():
        return Configuration.__new__(Configuration)

    @staticmethod
    def load_defaults():
        ''' configuration file defaults '''
        cfg = Configuration.__new__(Configuration)

        ## Main Configuration
        section = cfg.add_section('main')
        #EXAMPLE
        #section.add_option("services_package", "test.sample_services, test.sample_services2")
        #section.add_option("model_package", "test.dummy")
        section.add_option("mode", "DEV")
        section.add_option("applications", "[]")
        section.add_option("excluded_applications_from_worker", "[]")
        section.add_option("applications_in_worker", "[]")
        section.add_option("ip", "0.0.0.0")
        section.add_option("port", "8800")
        section.add_option("project_name", "MyProject")
        section.add_option("num_threads", "10")
        section.add_option("request_queue_size", "10")
        section.add_option("timeout", "10")
        section.add_option("store_type", Constants.MONGOENGINE)
        section.add_option("is_subdomain_aware", 'True')
        section.add_option("default_crypto_algorithm", Crypto.MD5)
        # default expire days for activation token
        section.add_option("default_expire_days", 7)
        #store configuration
        storeSection = cfg.add_section('store')
        storeSection.add_option("db_name", "c9")
        storeSection.add_option("ip", "127.0.0.1")
        storeSection.add_option("username", None)
        storeSection.add_option("password", None)
        storeSection.add_option("port", "27017")

        #Crypto Configuration
#        cryptoSection = cfg.add_section('crypto')
#        cryptoSection.add_option('hmac_secret', )
        # Global Cache Configuration

        memcacheSubSection = cfg.add_section("memcached")
        memcacheSubSection.add_option("servers", "127.0.0.1:11211")        
        # 0 means for ever
        memcacheSubSection.add_option("expireTime", 0)
        memcacheSubSection.add_option("min_compress_len", 0)

        cache = cfg.add_section("cache")
        cache.add_option("type", "memory")
        cache.add_option("url", "")
        cache.add_option("expire", 604800)
        cache.add_option("lock_dir", "/tmp/lock")
        cache.add_option("data_dir", "/tmp")

        #default sessions configuration
        sessionSection = cfg.add_section('session')
        sessionSection.add_option('type', Constants.MONGODB)
        sessionSection.add_option('cookie_expires', 'True')
        sessionSection.add_option('data_dir', 'tmp/')
        sessionSection.add_option('lock_dir', 'lock/')
        sessionSection.add_option('auto', 'True')
        sessionSection.add_option('cookie_expires', 'True')
        sessionSection.add_option('key', 'c9.session_id')
        sessionSection.add_option('url', ('%s/c9Session#session' % Constants.MONGODB_URL))
        sessionSection.add_option('secret', 'c9s3rc3t1234567890c9s3rc3t0987654321c9s3rc3t')
        sessionSection.add_option('secure', 'False')
        sessionSection.add_option('timeout', '600')
        return cfg

    @staticmethod
    def load_from_file_obj(fileObj, loadDefaults=True):
        cfg = ConfigParser.RawConfigParser()
        cfg.readfp(fileObj)
        if loadDefaults:
            cfgObj = Configuration.load_defaults()
        else:
            cfgObj = Configuration.create_empty_config()
        for section in cfg.sections():
            if cfgObj.has_section(section):
                secObj = cfgObj.get_section(section)
            else:
                secObj = cfgObj.add_section(section)
            for option in cfg.options(section):
                secObj.add_option(option, cfg.get(section, option))
        return cfgObj

    @staticmethod
    def load_file(file, loadDefaults=True):
        logging.info("loading configuration from file %s", file)
        if os.path.exists(file):
            fileObj = open(file)
            return Configuration.load_from_file_obj(fileObj, loadDefaults)
        else:
            raise RuntimeError("couldn't find the configuration file %s" % file)

    @staticmethod
    def dump_to_file_obj(fileObj, configObject):
        cfg = ConfigParser.RawConfigParser()
        for section in configObject.sections():
            secObj = configObject.get_section(section)
            cfg.add_section(section)
            for option in secObj.options():
                cfg.set(section, option, secObj.get_option(option))           
        cfg.write(fileObj)

    @staticmethod
    def dump_file(file, configObject=None):       
        logging.info("dumping configuration into file %s", file)
        cfgObj =  configObject or Configuration.load_defaults()
        with open(file, 'w') as configfile:
            Configuration.dump_to_file_obj(configfile, cfgObj)

    @staticmethod
    def create_instance(file=None):
        '''Creates new Configuration object with default configuration'''
        if file:
            return Configuration.load_file(file)
        return Configuration.load_defaults() 
    
