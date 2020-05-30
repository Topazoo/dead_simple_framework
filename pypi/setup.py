
"""Setup for the Dead Simple Framework"""

import setuptools

with open('README.md') as f:
    README = f.read()

setuptools.setup(
    author="Peter Swanson",
    author_email="peter.swanson@ucdavis.edu",
    name='dead_simple_framework',
    license="MIT",
    description='Specify APIs with a Python dict and run with one line',
    version='v0.2.5',
    long_description=README,
    url='https://github.com/Topazoo/dead_simple_framework',
    packages=setuptools.find_packages(),
    python_requires=">=3.5",
    install_requires=['flask', 'pymongo', 'celery', 'flask-cors', 'requests'],
    long_description_content_type='text/markdown',
    classifiers=[]
)