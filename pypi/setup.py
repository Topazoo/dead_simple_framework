
"""Setup for Dead Simple Framework"""

import setuptools

with open('README.md') as f:
    README = f.read()

setuptools.setup(
    author="Peter Swanson",
    author_email="pswanson@ucdavis.edu",
    name='dead_simple_framework',
    license="MIT",
    description='RESTful Flask framework with builtin MongoDB, Redis, Celery, Sentry and Slack integrations',
    version='v1.1.4',
    long_description=README,
    url='https://github.com/Topazoo/dead_simple_framework',
    packages=setuptools.find_packages(),
    python_requires=">=3.5",
    install_requires=['flask', 'pymongo', 'celery', 'flask-cors', 'requests', 'redis', 'eventlet', 'pyOpenSSL', 'Flask-JWT-Extended', 'passlib', 'jsonschema', 'sentry-sdk[flask]', 'slack-sdk'],
    long_description_content_type='text/markdown',
    classifiers=[]
)