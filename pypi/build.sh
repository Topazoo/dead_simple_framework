#! /bin/bash

rm -rf dist/ build/ dead_simple_framework.egg-info/
cp ../README.md .
python3 setup.py sdist bdist_wheel