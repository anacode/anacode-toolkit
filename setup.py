from setuptools import setup, find_packages


setup(
    name='anacode',
    version='0.5',
    description='Anacode GmbH aggregation library',
    author='Tomas Stibrany',
    author_email='tomas.stibrany@anacode.de',
    packages=find_packages(),
    install_requires=['requests', 'pandas', 'seaborn', 'matplotlib',
                      'wordcloud', 'pillow'],
    tests_require=['pytest', 'mock', 'pytest-mock', 'freezegun'],
)
