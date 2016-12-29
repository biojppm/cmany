#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os.path

def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        return f.read()

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
          "Topic :: Software Development :: Build Tools",
          "Topic :: Software Development :: Libraries :: Python Modules",
      ],
      keywords = ["cmake", "c", "c++"],
      author = "Joao Paulo Magalhaes",
      author_email = "dev@jpmag.me",
      zip_safe = False,
      namespace_packages = ['c4'],
      packages = find_packages('src'),
      package_dir = {'':'src'},
      entry_points = {'console_scripts':['cmany = c4.cmany.main:cmany_main'],},
      install_requires = ['setuptools'],
)
