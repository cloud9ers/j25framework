#!/bin/bash

#assuming the machine has virtualenv and pip installed
if [ ! -d cache ]
  then
   mkdir cache
fi

virtualenv --no-site-packages environment

export PYTHONPATH=

source environment/bin/activate
pip install --download-cache=cache  yolk nose

pip install --download-cache=cache -r requirements.pip
