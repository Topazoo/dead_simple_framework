#! /bin/bash

rm -rf dist/ build/ dead_simple_framework.egg-info/
cp ../README.md ../dead_simple_framework .
python3 setup.py sdist bdist_wheel
rm -rf dead_simple_framework/