#!/bin/sh

python3 -m pip install -r $PWD/requirements.txt
python3 $PWD/split.py $1

