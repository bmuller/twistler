#!/usr/bin/env python
try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

setup(
    name="twistler",
    version="0.1",
    description="Controller class extensions for Nevow",
    author="Brian Muller",
    author_email="bmuller@butterfat.net",
    license="GPLv3",
    url="http://trac.butterfat.net/public/twistler",
    packages=["twistler"],
    requires=["twisted", "nevow"]
)
