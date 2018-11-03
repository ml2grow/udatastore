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
    'umongo',
    'pymongo',
    'google-cloud-datastore>=1.7.0'
]

setup(
    name='udatastore',
    version=read_version("udatastore/_version.py"),
    url='https://github.com/ml2grow/udatastore',
    license="Apache License 2.0",
    author='javdrher',
    author_email='joachim@ml2grow.com',
    description='Datastore framework implementation for umongo',
    packages=find_packages(exclude=('tests*',)),
    extras_require={
        'test': ['nox']
    },
    include_package_data=True,
    install_requires=REQUIREMENTS,
)
