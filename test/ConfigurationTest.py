import unittest

import tempfile
from j25.Configuration import Configuration
from test.TestConfiguration import TestConfiguration

CONFIG_CONTENTS = '''[main]
ip = 127.0.0.1
port = 8888
[store]
type = mongo
ip = 127.0.0.1
dbName = c9
TEST = 5
'''

class ConfigurationTest(unittest.TestCase):
    def setUp(self):
        self.f = tempfile.NamedTemporaryFile()
        print >> self.f, CONFIG_CONTENTS
        self.f.flush()
        
    def tearDown(self):
        self.f.close()
    
    def testLoadingFromFileObj(self):
        fileObj = open(self.f.name)
        config = Configuration.load_from_file_obj(fileObj)
        self._testLoading(config)
        
    def testLoadingFromFile(self):
        config = Configuration.load_file(self.f.name)
        self._testLoading(config)
        
    def testDefaults(self):
        config = Configuration.load_defaults()
        self.assertTrue(hasattr(config, "main"))
        self.assertEquals("0.0.0.0", config.main.ip)
        self.assertEquals(8800, int(config.main.port))
        self.assertEquals(10, int(config.main.num_threads))
        
        self.assertTrue(hasattr(config, "memcached"))
        self.assertEquals("127.0.0.1:11211", config.memcached.servers)
        self.assertEquals(0, config.memcached.expireTime)
        self.assertEquals(0, config.memcached.min_compress_len)
                
    def testDefaultsOverlaying(self):
        config = Configuration.load_file(self.f.name)
        self.assertTrue(hasattr(config, "main"))
        self.assertEquals("127.0.0.1", config.main.ip)
        self.assertEquals(8888, int(config.main.port))
        self.assertEquals(10, int(config.main.num_threads))
        
    def _testLoading(self, config):
        self.assertTrue(hasattr(config, "main"))
        self.assertEquals("127.0.0.1", config.main.ip)
        self.assertEquals(8888, int(config.main.port))
        self.assertTrue(hasattr(config, "store"))
        self.assertEquals("mongo", config.store.type)
        self.assertEquals("127.0.0.1", config.store.ip)
        self.assertEquals("c9", config.store.dbname)
        self.assertFalse(hasattr(config.store, "TEST"))
        self.assertEquals("5", config.store.test)
    
    def testDumpFile(self):
        fileObj = tempfile.NamedTemporaryFile()
        fileName = fileObj.name
        configObj = TestConfiguration.create_instance()
        Configuration.dump_file(fileName, configObj)
        loadedCfg = Configuration.load_file(fileName)        
        # comparing cfg and configObj        
        self.assertEquals(sorted(loadedCfg.sections()), sorted(configObj.sections()))
        
        configObjDict = {}
        ConfigFileDict = {}
        configObjOptions = []
        ConfigFileOptions = []
        
        for section in configObj.sections():
            secObj = configObj.get_section(section)
            configObjOptions.extend(secObj.options())
            tempOptionsDict = {}
            for option in secObj.options():
                tempOptionsDict[option] =  secObj.get_option(option)
            configObjDict[section] = tempOptionsDict
                                
        for section in loadedCfg.sections():
            secObj = configObj.get_section(section)
            ConfigFileOptions.extend(secObj.options())
            tempOptionsDict = {}
            for option in secObj.options():
                tempOptionsDict[option] =  secObj.get_option(option)
            ConfigFileDict[section] = tempOptionsDict
        
        self.assertTrue(configObjOptions)
        self.assertTrue(ConfigFileOptions)  
        self.assertTrue(ConfigFileDict)
        self.assertTrue(configObjDict)
        self.assertEquals(sorted(configObjOptions), sorted(ConfigFileOptions))     
        self.assertEquals(len(ConfigFileDict), len(configObjDict))
        
        for k, v in configObjDict.iteritems():
            self.assertEquals(v, ConfigFileDict[k])
        
        for k, v in ConfigFileDict.iteritems():
            self.assertEquals(v, configObjDict[k])