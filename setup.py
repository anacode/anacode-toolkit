from setuptools import setup, find_packages


setup(
    name='anacode',
    version='1.0',
    description='Anacode API querying and aggregation library',
    author='Tomas Stibrany',
    author_email='tomas.stibrany@anacode.de',
    url='https://github.com/anacode/anacode-toolkit',
    download_url='https://github.com/anacode/anacode-toolkit/tarball/1.0',
    license='BSD-3-Clause',
    keywords=['anacode', 'nlp', 'chinese'],
    packages=find_packages(),
    install_requires=['requests', 'pandas', 'seaborn', 'matplotlib',
                      'wordcloud', 'pillow', 'nltk'],
    tests_require=['pytest', 'mock', 'pytest-mock', 'freezegun'],
    classifiers=[],
)
