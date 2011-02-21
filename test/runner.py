from bin import Server
from nose.loader import TestLoader
from nose.plugins.manager import DefaultPluginManager
from nose.suite import LazySuite
from nose_cov import Cov
import logging
import nose
import optparse
import os
import sys
import re

logLevelsMap = {"DEBUG": logging.DEBUG,
                "INFO" : logging.INFO,
                "WARN" : logging.WARN,
                "ERROR": logging.ERROR
                }

def createFQSuite(fqTestNames):
    return LazySuite(TestLoader().loadTestsFromNames(fqTestNames))

def loadTestsFromDir(dir):
    config = nose.core.Config()
    config.testMatch = re.compile('.*[Tt]est')
    generator = TestLoader(config).loadTestsFromDir(dir)
    return LazySuite(generator)       

def main(runner):
    defaultDir = os.getcwd()
    modes = 0   
    parser = optparse.OptionParser()
    
    parser.add_option("-l", "--logging", dest="logging", default="INFO", help="Set logging level")
    parser.add_option("-c", "--count", dest="count", default="1", help="Run test cases for <COUNT> times")
    parser.add_option("-d", "--directory", dest="directory", default=False, help="Run test cases in specific directory")
    parser.add_option("-p", "--package", dest="package", default=False, help="Run test cases in a specific package")
    env = os.environ
    conf = runner.config
    cov  = Cov()
    cov.enabled = True
    cov.options(parser, env)
    source = defaultDir[:defaultDir.rfind('/')]
    parser.set_default('cov_source', [source])
  
    options, fqTestNames = parser.parse_args() 
    Server.setupLogging(logLevelsMap[options.logging])
    if options.enable_plugin_cov: 
        cov.configure(options, conf)
        cov.begin()
        covaragePlugin = DefaultPluginManager()
        covaragePlugin.addPlugin(cov)
        conf.plugins = covaragePlugin
        
    logging.info("Started with argv=%s", str(sys.argv))

    if options.package:
        modes += 1
        path = defaultDir+os.sep+options.package
        testSuite = loadTestsFromDir(path)
        
    if options.directory:
        modes += 1
        testSuite = loadTestsFromDir(options.directory)
        
    if modes > 1:
        parser.print_help(sys.stderr)
        exit(os.EX_USAGE)
    if modes == 0:
        if len(fqTestNames) == 0:
            testSuite = loadTestsFromDir(defaultDir)
        else:
            testSuite = createFQSuite(fqTestNames)
    for _ in xrange(int(options.count)):
        runner.run(testSuite)
    
if __name__ == '__main__':
    main(nose.core.TextTestRunner())
