from bin import Server
from nose.loader import TestLoader
from nose.plugins.manager import DefaultPluginManager
from nose.suite import LazySuite
#from nose_cov import Cov
import logging
import nose
import optparse
import os
import sys
import re

def createFQSuite(fqTestNames):
    return LazySuite(TestLoader().loadTestsFromNames(fqTestNames))

def loadTestsFromDir(dir):
    config = nose.core.Config()
    config.testMatch = re.compile('.*[Tt]est')
    generator = TestLoader(config).loadTestsFromDir(dir)
    return LazySuite(generator) 

def main(runner):
    parser = optparse.OptionParser()
    options, args = parser.parse_args()
    args.pop(0)
    projectDir = os.path.join(os.path.abspath("."))
    appsDir = os.path.join(projectDir, "apps")
    if len(args)== 0:
        for x in os.listdir(appsDir):
            if os.path.isdir(os.path.join(appsDir, x)):
                testSuite = loadTestsFromDir(os.path.join(appsDir, x, 'tests'))
                runner.run(testSuite)
    else:
        if os.path.isdir(os.path.join('apps',args[0])):
            os.chdir('apps')
        testSuite = createFQSuite(args)
        runner.run(testSuite)
            
            