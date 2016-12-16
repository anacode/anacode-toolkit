from setuptools import setup, find_packages


setup(
    name='anacode',
    version='0.1',
    description='Anacode GmbH aggregation library',
    author='Tomas Stibrany',
    author_email='tomas.stibrany@anacode.de',
    packages=find_packages(),
    install_requires=['requests', 'pandas', 'seaborn', 'matplotlib'],
    tests_require=['pytest', 'mock', 'freezegun'],
)
