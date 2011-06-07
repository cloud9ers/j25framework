from nose.core import TestProgram
from j25.scripts import Server
import logging, os, sys

libs = os.path.join('..', os.path.pardir, 'lib')
sys.path.insert(0, libs)

Server.setupLogging(logging.INFO)
TestProgram()