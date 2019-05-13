# Copyright 2019 ML2Grow NV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
from setuptools import setup, find_packages


def read_version(fname):
    verstrline = open(fname, "rt").read()
    vsre = r"^__version__ = ['\"]([^'\"]*)['\"]"
    matched = re.search(vsre, verstrline, re.M)
    if matched:
        return matched.group(1)
    else:
        raise RuntimeError("Unable to find version string in %s." % (fname,))


REQUIREMENTS = [
    'umongo>=1.2.0,<1.3',
    'pymongo>=3.7.2,<3.8',
    'google-cloud-datastore>=1.7.0,<1.8'
]

with open('README.md') as f:
    README = f.read()

setup(
    name='udatastore',
    version=read_version("udatastore/_version.py"),
    url='https://github.com/ml2grow/udatastore',
    license="Apache License 2.0",
    author='javdrher',
    author_email='joachim@ml2grow.com',
    description='Datastore framework implementation for umongo',
    long_description=README,
    long_description_content_type='text/markdown',
    packages=find_packages(exclude=('tests*',)),
    extras_require={
        'test': ['nox']
    },
    include_package_data=True,
    install_requires=REQUIREMENTS,
    test_suite='tests',
    keywords='udatastore umongo pymongo datastore',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ]
)
