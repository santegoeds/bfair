#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name = "bfair",
    version = "0.1",
    packages = find_packages(exclude = ["tests"]),
    install_requires = ["suds>=0.4"],
    tests_require=["pytest"],

    author = "Tjerk Santegoeds",
    author_email = "tsan@tdias.com",
    description = "Betfair API",
    license = "Apache Version 2.0",
    keywords = "betfair",
    url = "santegoeds.github.com/bfair",
)

