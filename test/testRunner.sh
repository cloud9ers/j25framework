#!/bin/bash
export PYTHONPATH=`dirname $0`/..:$PYTHONPATH
python runner.py $*
