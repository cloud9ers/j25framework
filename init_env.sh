#!/bin/bash

#assuming the machine has virtualenv and pip installed

virtualenv --no-site-packages environment

export PYTHONPATH=
source environment/bin/activate

pip install  yolk nose

pip install -r requirements.pip
