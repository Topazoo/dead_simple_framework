
"""Setup for Dead Simple Framework"""

import setuptools

with open('README.md') as f:
    README = f.read()

setuptools.setup(
    author="Peter Swanson",
    author_email="pswanson@ucdavis.edu",
    name='dead_simple_framework',
    license="MIT",
    description='RESTful Flask framework with MongoDB, Redis and Celery integrations',
    version='v0.8.7',
    long_description=README,
    url='https://github.com/Topazoo/dead_simple_framework',
    packages=setuptools.find_packages(),
    python_requires=">=3.5",
    install_requires=['flask', 'pymongo', 'celery', 'flask-cors', 'requests', 'redis', 'eventlet', 'pyOpenSSL', 'Flask-JWT-Extended', 'passlib', 'jsonschema'],
    long_description_content_type='text/markdown',
    classifiers=[]
)