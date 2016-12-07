from setuptools import setup


setup(
    name='anacode',
    version='0.1',
    description='Anacode GmbH aggregation library',
    author='Tomas Stibrany',
    author_email='tomas.stibrany@anacode.de',
    install_requires=['requests'],
    tests_require=['pytest', 'mock', 'freezegun'],
)
