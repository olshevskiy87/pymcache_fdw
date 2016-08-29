import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='pymcache_fdw',
    version='0.0.10',
    description=('memcache fdw for postgresql'),
    long_description=read('README.md'),
    author='Dmitriy Olshevskiy',
    author_email='olshevskiy87@bk.ru',
    license='MIT',
    keywords='memcache postgres pgsql fdw wrapper',
    packages=['pymcache_fdw'],
    install_requires=['pymemcache'],
    url='https://github.com/olshevskiy87/pymcache_fdw'
)
