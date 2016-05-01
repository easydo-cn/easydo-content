################################
import os
import xml.sax.saxutils
from setuptools import setup, find_packages

def read(*rnames):
    text = open(os.path.join(os.path.dirname(__file__), *rnames)).read()
    return xml.sax.saxutils.escape(text)

setup (
    name='easydo_content',
    version='0.1.0dev',
    author = "panjy",
    author_email = "panjy@gmail.com",
    description = "",
    long_description=( read('README.md') ),
    license = "Private",
    keywords = "edo",
    classifiers = [
        'Development Status :: 4 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Natural Language :: Chinese',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Framework :: Zope3'],
    url = 'http://epk.zopen.cn/pypi/edo_content',
    packages = find_packages(),
    include_package_data = True,
    zip_safe = False,
)

