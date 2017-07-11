"""
Usage:
    python setup.py py2app

"""

from setuptools import setup

APP = ['GFM.py']


setup(
    app = APP,
    setup_requires = ['py2app'],
)
