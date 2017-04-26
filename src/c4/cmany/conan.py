
from ruamel import yaml
import os.path
from collections import OrderedDict as odict

from . import util


class Conan:

    def __init__(self):
        util.cacheattr(Conan, 'settings', Conan.load_settings)

    def install(self, build):
        with util.setcwd(build.builddir, silent=False):
            cmd = (['conan', 'install', '--build=missing'] +
                   self.translate_os(build.system) +
                   self.translate_architecture(build.architecture) +
                   self.translate_compiler(build.compiler) +
                   self.translate_buildtype(build.build_type) +
                   [os.path.abspath(build.projdir)])
            util.runsyscmd(cmd)

    @staticmethod
    def load_settings():
        conandir = os.path.expanduser("~/.conan/")
        if not os.path.exists(conandir):
            return
        settings_file = os.path.join(conandir, 'settings.yml')
        with open(settings_file) as f:
            txt = f.read()
            data = yaml.load(txt, yaml.RoundTripLoader)
            settings = odict(data)
            return settings

    def translate_os(self, system):
        s = system.name
        if s == 'windows':
            s = 'Windows'
        conan = Conan.settings['os']
        if s in conan:
            return ['-s', 'os=' + s]
        msg = "system not found in conan: {}. Must be one of {}"
        raise Exception(msg.format(s, conan))

    def translate_architecture(self, architecture):
        s = architecture.name
        conan = Conan.settings['arch']
        if s in conan:
            return ['-s', 'arch=' + s]
        msg = "architecture not found in conan: {}. Must be one of {}"
        raise Exception(msg.format(s, conan))

    def translate_compiler(self, compiler):
        s = compiler.name
        if compiler.is_msvc:
            return ['-s', 'compiler=Visual Studio',
                    '-s', 'compiler.version='+str(compiler.vs.ver)]
        elif compiler.shortname == 'gcc':
            libcxx = 'libstdc++11'  # FIXME
            return ['-s', 'compiler=gcc',
                    '-s', 'compiler.version=' + str(compiler.version),
                    '-s', 'compiler.libcxx=' + str(libcxx)]
        conan = Conan.settings['compiler']
        if s in conan:
            return ['-s', 'compiler=' + s]
        msg = "compiler not found in conan: {}. Must be one of {}"
        raise Exception(msg.format(s, conan))

    def translate_build_type(self, build_type):
        s = build_type.name
        conan = Conan.settings['build_type']
        if s in conan:
            return ['-s', 'build_type=' + s]
        msg = "build type not found in conan: {}. Must be one of {}"
        raise Exception(msg.format(s, conan))

    def translate_variant(self, variant):
        return []
