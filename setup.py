#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from distutils.command.install import INSTALL_SCHEMES
from setuptools import setup, find_packages
import os.path
import sys
import glob

minversion = (3, 6)


if sys.version_info < minversion:
    # require at least 3.6 because of f-strings
    sys.exit(f'cmany requires at least Python {minversion}. Current version is {sys.version_info}. Sorry.')


# allows installing the data files side-by-side with the .py files
# https://stackoverflow.com/a/3042436
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']


def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        return f.read()


def get_readme():
    # skip the badge section
    contents = read('README.rst')
    s1 = "\ncmany\n====="
    s2 = "\ncmany\r\n====="
    i = contents.find(s1)
    if i == -1:
        i = contents.find(s2)
    if i == -1:
        raise Exception("malformed README")
    return contents[i:]


def readreqs(*rnames):
    def _skipcomment(line):
        return line if (line and not line.startswith('--')
                        and not line.startswith('#')) else ""
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        l = [_skipcomment(line.strip()) for line in f]
    return l


def get_data_files():
    # dest = get_binaries_directory()
    d = lambda d: d # os.path.join(dest, d)
    df = [
          (d("c4/cmany"), [
              "LICENSE.txt",
              "README.rst",
              "requirements.txt",
              "requirements_test.txt"
          ]),
          (d("c4/cmany/conf"), [
              "src/c4/cmany/conf/cmany.yml"
          ]),
          (d("c4/cmany/doc"),
              glob.glob("src/c4/cmany/doc/*.txt")
          ),
      ]
    return df


setup(name="cmany",
      version="0.1.3",
      description="CMake build tree batching tool",
      long_description=get_readme() + "\n" + read('LICENSE.txt'),
      url="https://github.com/biojppm/cmany",
      download_url="https://github.com/biojppm/cmany",
      license="License :: OSI Approved :: MIT License",
      classifiers=[
          "License :: OSI Approved :: MIT License",
          "Intended Audience :: Developers",
          "Development Status :: 3 - Alpha",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: 3.8",
          "Programming Language :: C",
          "Programming Language :: C++",
          "Topic :: Software Development :: Build Tools",
          "Topic :: Software Development :: Compilers",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "Topic :: Utilities",
      ],
      keywords=["cmake", "c++", "c"],
      author="Joao Paulo Magalhaes",
      author_email="dev@jpmag.me",
      zip_safe=False,
      namespace_packages=['c4'],
      packages=find_packages('src'),
      package_dir={'': 'src'},
      entry_points={'console_scripts': ['cmany=c4.cmany.main:cmany_main'], },
      install_requires=readreqs('requirements.txt'),
      tests_require=readreqs('requirements_test.txt'),
      test_suite='nose.collector',
      include_package_data=True,
      # package_data={'c4.cmany':read_manifest()},
      data_files=get_data_files(),
)
