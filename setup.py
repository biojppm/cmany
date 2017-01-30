#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os.path
import sys
import re


if sys.version_info < (3, 4):
    # this is because of unittest.subTest()
    msg = 'cmany requires at least Python 3.4. Current version is {}. Sorry.'
    sys.exit(msg.format(sys.version_info))
if sys.version_info < (3, 3):
    # this is because of subprocess. That code is in c4/cmany/util.py.
    msg = 'cmany requires at least Python 3.3. Current version is {}. Sorry.'
    sys.exit(msg.format(sys.version_info))


def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        return f.read()


def read_manifest():
    thisd = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(thisd, 'MANIFEST.in')) as f:
        lines = [ re.sub(r'include (.*)$', r'\1', l) for l in f.readlines() ]
        lines = [ os.path.join(thisd, l) for l in lines ]
        print(lines)
        return lines


def readreqs(*rnames):
    def _skipcomment(line):
        return line if (line and not line.startswith('--')
                        and not line.startswith('#')) else ""
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        l = [_skipcomment(line.strip()) for line in f]
    return l


setup(name="cmany",
      version="0.1",
      description="CMake build tree batching tool",
      long_description=read('README.rst'),
      url="https://github.com/biojppm/cmany",
      download_url="https://github.com/biojppm/cmany",
      license="License :: OSI Approved :: MIT License",
      classifiers=[
          "License :: OSI Approved :: MIT License",
          "Intended Audience :: Developers",
          "Development Status :: 2 - Pre-Alpha",
          "Programming Language :: Python :: 3",
          "Programming Language :: C",
          "Programming Language :: C++",
          "Topic :: Software Development :: Build Tools",
          "Topic :: Software Development :: Compilers",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "Topic :: Utilities",
      ],
      keywords=["cmake", "c", "c++"],
      author="Joao Paulo Magalhaes",
      author_email="dev@jpmag.me",
      zip_safe=False,
      namespace_packages=['c4'],
      packages=find_packages('src'),
      package_dir={'': 'src'},
      entry_points={'console_scripts': ['cmany=c4.cmany.main:cmany_main'], },
      install_requires=readreqs('requirements.txt'),
      tests_require=readreqs('requirements_test.txt'),
      include_package_data=True,
      package_data={'c4.cmany':read_manifest()}
)
