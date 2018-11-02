import re
from setuptools import setup, find_packages


VERSIONFILE="udatastore/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))


REQUIREMENTS = [
    'umongo',
    'pymongo',
    'google-cloud-datastore>=1.7.0'
]

setup(
    name='udatastore',
    version=verstr,
    url='https://github.com/ml2grow/udatastore',
    license="Apache License 2.0",
    author='javdrher',
    author_email='joachim@ml2grow.com',
    description='Datastore framework implementation for umongo',
    packages=find_packages(exclude=('tests*',)),
    extras_require={
        'test': ['nox-automation']
    },
    include_package_data=True,
    install_requires=REQUIREMENTS,
)
