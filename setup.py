#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os.path
import sys
import site
import glob


if sys.version_info < (3, 4):
    # python 3.3 is no longer supported by pip
    msg = 'cmany requires at least Python 3.4. Current version is {}. Sorry.'
    sys.exit(msg.format(sys.version_info))


def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        return f.read()


def readreqs(*rnames):
    def _skipcomment(line):
        return line if (line and not line.startswith('--')
                        and not line.startswith('#')) else ""
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        l = [_skipcomment(line.strip()) for line in f]
    return l


def get_binaries_directory():
    """Return the installation directory, or None
    http://stackoverflow.com/questions/36187264"""
    if '--user' in sys.argv:
        paths = (site.getusersitepackages(),)
    else:
        if hasattr(site, 'getsitepackages'):
            print("cmany setup: site-packages", site.getsitepackages())
            print("cmany setup: site-user-packages", site.getusersitepackages())
            print("cmany setup: site-prefix", os.path.dirname(sys.executable))
            paths = site.getsitepackages()
        else:
            print("cmany setup: no site.getsitepackages()...")
            py_prefix = os.path.dirname(sys.executable)
            paths = [
                py_prefix + '/lib/site-packages',
                py_prefix + '/lib/site-packages',
                py_prefix + '/lib',
            ]
        py_version = '{}.{}'.format(sys.version_info[0], sys.version_info[1])
        paths += (s.format(py_version) for s in (
            sys.prefix + '/lib/python{}/site-packages/',
            sys.prefix + '/lib/python{}/dist-packages/',
            sys.prefix + '/local/lib/python{}/site-packages/',
            sys.prefix + '/local/lib/python{}/dist-packages/',
            '/Library/Python/{}/site-packages/',
        ))
    for path in paths:
        if os.path.exists(path):
            print('cmany setup: installation path:', path)
            return path
    raise Exception('cmany setup: no installation path found', file=sys.stderr)
    return None


def get_data_files():
    # dest = get_binaries_directory()
    d = lambda d: "share/" + d # os.path.join(dest, d)
    df = [
          (d("c4/cmany"), [
              "LICENSE.txt",
              "README.rst",
              "requirements.txt",
              "requirements_test.txt"
          ]),
          (d("c4/cmany/conf"), [
              "conf/cmany.yml"
          ]),
          (d("c4/cmany/doc"),
              glob.glob("doc/_build/text/*.txt")
          ),
      ]
    return df


setup(name="cmany",
      version="0.1.2",
      description="CMake build tree batching tool",
      long_description=read('README.rst') + "\n" + read('LICENSE.txt'),
      url="https://github.com/biojppm/cmany",
      download_url="https://github.com/biojppm/cmany",
      license="License :: OSI Approved :: MIT License",
      classifiers=[
          "License :: OSI Approved :: MIT License",
          "Intended Audience :: Developers",
          "Development Status :: 3 - Alpha",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
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
