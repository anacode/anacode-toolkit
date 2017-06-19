from setuptools import setup, find_packages


setup(
    name='anacode',
    version='v1.1.1',
    description='Anacode API querying and aggregation library',
    author='Tomas Stibrany',
    author_email='tomas.stibrany@anacode.de',
    url='https://github.com/anacode/anacode-toolkit',
    download_url='https://github.com/anacode/anacode-toolkit/tarball/v1.1.1',
    license='BSD-3-Clause',
    keywords=['anacode', 'nlp', 'chinese'],
    packages=find_packages(),
    install_requires=['requests', 'pandas', 'seaborn', 'matplotlib',
                      'wordcloud', 'pillow', 'nltk'],
    tests_require=['pytest', 'mock', 'pytest-mock', 'freezegun', 'notebook',
                   'ipywidgets'],
    classifiers=[],
)
