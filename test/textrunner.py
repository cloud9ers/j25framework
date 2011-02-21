from nose.core import TestProgram
from bin import Server
import logging

Server.setupLogging(logging.INFO)
TestProgram()