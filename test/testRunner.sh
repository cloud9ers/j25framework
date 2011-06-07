#!/bin/bash
export PYTHONPATH=`dirname $0`/..:`dirname $0`/../lib/mongodb_beaker-0.1-py2.6.egg:$PYTHONPATH
python runner.py $*
