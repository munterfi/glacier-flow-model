"""
Usage:
    python setup.py py2app

"""
import sys
from setuptools import setup

sys.setrecursionlimit(1500)

APP = ['src/GFM.py']
OPTIONS = {
    'iconfile':'docs/GFM.icns'
    }

setup(
    app = APP,
    setup_requires = ['py2app'],
)
