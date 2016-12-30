from setuptools import setup, find_packages


setup(
    name='anacode',
    version='0.5',
    description='Anacode GmbH querying and aggregation library',
    author='Tomas Stibrany',
    author_email='tomas.stibrany@anacode.de',
    url='https://github.com/anacode/anacode-toolkit',
    license='BSD-3-Clause',
    keywords='anacode',
    packages=find_packages(),
    install_requires=['requests', 'pandas', 'seaborn', 'matplotlib',
                      'wordcloud', 'pillow'],
    tests_require=['pytest', 'mock', 'pytest-mock', 'freezegun'],
)
