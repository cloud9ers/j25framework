#!/bin/bash
source ../environment/bin/activate
source ../setenv.sh
nosetests --with-xunit
exit 0
