import re
from setuptools import setup, find_packages


VERSIONFILE="ml2grow/framework/ugrow/_version.py"
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
    name='ml2grow-framework-ugrow',
    version=verstr,
    url='https://gitlab.ml2grow.com/python-libs/ugrow',
    license='ML2Grow proprietary',
    author='javdrher',
    author_email='joachim@ml2grow.com',
    description='ML2Grow umongo datastore plugin',
    namespace_packages =[
        'ml2grow',
        'ml2grow.framework'
    ],
    packages=find_packages(exclude=('tests*',)),
    include_package_data=True,
    install_requires=REQUIREMENTS,
)
