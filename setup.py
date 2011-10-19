#!/usr/bin/env python
#
#  Copyright 2011 Tjerk Santegoeds
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

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

