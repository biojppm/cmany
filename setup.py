#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages, Extension
import os.path


def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        return f.read()


def readreqs(*rnames):
    def _skipcomment(line):
        return line if (line and not line.startswith('--') and not line.startswith('#')) else ""
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        l = [_skipcomment(line.strip()) for line in f]
    return l


setup(name = "cmany",
      version = "0.1",
      description = "CMake build tree batching tool",
      long_description = read('README.rst'),
      url = "https://github.com/biojppm/cmany",
      download_url = "https://github.com/biojppm/cmany",
      license = "License :: OSI Approved :: MIT License",
      classifiers = [
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
      keywords = ["cmake", "c", "c++"],
      author = "Joao Paulo Magalhaes",
      author_email = "dev@jpmag.me",
      zip_safe = False,
      namespace_packages = ['c4'],
      packages = find_packages('src'),
      package_dir = {'':'src'},
      entry_points = {'console_scripts':['cmany = c4.cmany.main:cmany_main'],},
      install_requires = readreqs('requirements.txt'),
      tests_require = readreqs('requirements_test.txt'),
      #include_package_data = True,
      #package_data = {'c4.cmany':['test/*','test/*/*']}
)
