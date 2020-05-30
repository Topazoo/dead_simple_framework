#! /bin/bash

rm -rf dist/ build/ dead_simple_framework.egg-info/ dead_simple_framework/ README.md
cp -r ../README.md ../dead_simple_framework .
python3 setup.py sdist bdist_wheel