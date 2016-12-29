#!/usr/bin/env python3

import os
import re
import glob
import json

from .util import *
from .cmake_sysinfo import *

is64 = "64" in CMakeSysInfo.architecture()

# -----------------------------------------------------------------------------
class VisualStudioInfo:
    """encapsulates info on Visual Studio installations"""

    # This class was previously in a multi-purpose module, and that's why
    # many of the methods here are static. Now that this logic is in a 
    # dedicated module, the static properties and methods should be
    # moved outside of the class to become module members.

    order = ('vs2015','vs2017','vs2013','vs2012','vs2010','vs2008','vs2005',)
    # a reversible dictionary for the VS version numbers
    _versions = {
        'vs2015':14, 14:'vs2015', 'vs2015_64':14, 'vs2015_32':14, 'vs2015_arm':14 ,  # nopep8
        'vs2017':15, 15:'vs2017', 'vs2017_64':15, 'vs2017_32':15, 'vs2017_arm':15 ,  # nopep8
        'vs2013':12, 12:'vs2013', 'vs2013_64':12, 'vs2013_32':12, 'vs2013_arm':12 ,  # nopep8
        'vs2012':11, 11:'vs2012', 'vs2012_64':11, 'vs2012_32':11, 'vs2012_arm':11 ,  # nopep8
        'vs2010':10, 10:'vs2010', 'vs2010_64':10, 'vs2010_32':10, 'vs2010_ia64':10,  # nopep8
        'vs2008':9 , 9 :'vs2008', 'vs2008_64':9 , 'vs2008_32':9 , 'vs2008_ia64':9 ,  # nopep8
        'vs2005':8 , 8 :'vs2005', 'vs2005_64':8 , 'vs2005_32':8 ,   # nopep8
    }
    _sfx = ' Win64' if is64 else ''
    # a reversible dictionary for the names
    _names = {
        'vs2017'      : 'Visual Studio 15 2017' + _sfx , 'Visual Studio 15 2017' + _sfx : 'vs2017'      ,  # nopep8
        'vs2017_32'   : 'Visual Studio 15 2017'        , 'Visual Studio 15 2017'        : 'vs2017_32'   ,  # nopep8
        'vs2017_64'   : 'Visual Studio 15 2017 Win64'  , 'Visual Studio 15 2017 Win64'  : 'vs2017_64'   ,  # nopep8
        'vs2017_arm'  : 'Visual Studio 15 2017 ARM'    , 'Visual Studio 15 2017 ARM'    : 'vs2017_arm'  ,  # nopep8
        'vs2015'      : 'Visual Studio 14 2015' + _sfx , 'Visual Studio 14 2015' + _sfx : 'vs2015'      ,  # nopep8
        'vs2015_32'   : 'Visual Studio 14 2015'        , 'Visual Studio 14 2015'        : 'vs2015_32'   ,  # nopep8
        'vs2015_64'   : 'Visual Studio 14 2015 Win64'  , 'Visual Studio 14 2015 Win64'  : 'vs2015_64'   ,  # nopep8
        'vs2015_arm'  : 'Visual Studio 14 2015 ARM'    , 'Visual Studio 14 2015 ARM'    : 'vs2015_arm'  ,  # nopep8
        'vs2013'      : 'Visual Studio 12 2013' + _sfx , 'Visual Studio 12 2013' + _sfx : 'vs2013'      ,  # nopep8
        'vs2013_32'   : 'Visual Studio 12 2013'        , 'Visual Studio 12 2013'        : 'vs2013_32'   ,  # nopep8
        'vs2013_64'   : 'Visual Studio 12 2013 Win64'  , 'Visual Studio 12 2013 Win64'  : 'vs2013_64'   ,  # nopep8
        'vs2013_arm'  : 'Visual Studio 12 2013 ARM'    , 'Visual Studio 12 2013 ARM'    : 'vs2013_arm'  ,  # nopep8
        'vs2012'      : 'Visual Studio 11 2012' + _sfx , 'Visual Studio 11 2012' + _sfx : 'vs2012'      ,  # nopep8
        'vs2012_32'   : 'Visual Studio 11 2012'        , 'Visual Studio 11 2012'        : 'vs2012_32'   ,  # nopep8
        'vs2012_64'   : 'Visual Studio 11 2012 Win64'  , 'Visual Studio 11 2012 Win64'  : 'vs2012_64'   ,  # nopep8
        'vs2012_arm'  : 'Visual Studio 11 2012 ARM'    , 'Visual Studio 11 2012 ARM'    : 'vs2012_arm'  ,  # nopep8
        'vs2010'      : 'Visual Studio 10 2010' + _sfx , 'Visual Studio 10 2010' + _sfx : 'vs2010'      ,  # nopep8
        'vs2010_32'   : 'Visual Studio 10 2010'        , 'Visual Studio 10 2010'        : 'vs2010_32'   ,  # nopep8
        'vs2010_64'   : 'Visual Studio 10 2010 Win64'  , 'Visual Studio 10 2010 Win64'  : 'vs2010_64'   ,  # nopep8
        'vs2010_ia64' : 'Visual Studio 10 2010 IA64'   , 'Visual Studio 10 2010 IA64'   : 'vs2010_ia64' ,  # nopep8
        'vs2008'      : 'Visual Studio 8 2008' + _sfx  , 'Visual Studio 8 2008' + _sfx  : 'vs2008'      ,  # nopep8
        'vs2008_32'   : 'Visual Studio 8 2008'         , 'Visual Studio 8 2008'         : 'vs2008_32'   ,  # nopep8
        'vs2008_64'   : 'Visual Studio 8 2008 Win64'   , 'Visual Studio 8 2008 Win64'   : 'vs2008_64'   ,  # nopep8
        'vs2008_ia64' : 'Visual Studio 8 2008 IA64'    , 'Visual Studio 8 2008 IA64'    : 'vs2008_ia64' ,  # nopep8
        'vs2005'      : 'Visual Studio 5 2005' + _sfx  , 'Visual Studio 5 2005' + _sfx  : 'vs2005'      ,  # nopep8
        'vs2005_32'   : 'Visual Studio 5 2005'         , 'Visual Studio 5 2005'         : 'vs2005_32'   ,  # nopep8
        'vs2005_64'   : 'Visual Studio 5 2005 Win64'   , 'Visual Studio 5 2005 Win64'   : 'vs2005_64'   ,  # nopep8
    }

    _toolsets = (
        # vs2017 compiler toolsets
        'v141_clang_c2', 'v141_clang', 'v141_xp', 'v141',
        # vs2015 compiler toolsets
        'v140_clang_c2', 'v140_clang', 'v140_xp', 'v140',
        # vs2013 compiler toolsets
        'v120_xp', 'v120',
        # vs2013 compiler toolsets
        'v110_xp', 'v110',
        # vs2013 compiler toolsets
        'v100_xp', 'v100',
        # aliases - implicit compiler toolsets (the same as the chosen VS version)
        'clang_c2', 'clang', 'xp',
    )
    _toolsets_for_re = sorted(_toolsets, key=lambda x: -len(x))

    @staticmethod
    def sep_name_toolset(name, canonize=True):
        toolset = None
        for t in __class__._toolsets_for_re:
            rx = r'vs.....*_({})$'.format(t)
            if re.search(rx, name):
                toolset = re.sub(rx, r'\1', name)
                name_without_toolset = re.sub(r'(vs.....*)_({})$'.format(t), r'\1', name)
                break
        if toolset is None:
            return name,None
        if toolset not in __class__._toolsets:
            raise Exception("could not parse toolset {} from vs spec {}".format(toolset, name))
        if not canonize:
            return name_without_toolset, toolset
        if toolset in ('clang_c2', 'clang', 'xp'):
            assert re.match('vs....', name)
            year = int(re.sub(r'^vs(....).*', r'\1', name))
            if year == 2017:
                vs_toolset = 'v141_' + toolset
            elif year == 2015:
                vs_toolset = 'v140_' + toolset
            else:
                assert toolset != "clang"
                if year == 2013:
                    vs_toolset = 'v120_' + toolset
                elif year == 2012:
                    vs_toolset = 'v110_' + toolset
                elif year == 2010:
                    vs_toolset = 'v100_' + toolset
                else:
                    raise Exception("toolset not implemented for " + name + ". toolset="+toolset)
        else:
            vs_toolset = toolset
        if vs_toolset.endswith('clang'):
            vs_toolset += '_c2'
        return name_without_toolset, vs_toolset

    @staticmethod
    def parse_toolset(name, canonize=True):
        _, toolset = __class__.sep_name_toolset(name, canonize)
        return toolset

    def __init__(self, name):
        cn, toolset = __class__.sep_name_toolset(name)
        if cn not in __class__._versions.keys():
            raise Exception("unknown alias: " + name)
        ver = __class__._versions[cn]
        self.name = name
        self.name_without_toolset = cn
        self.toolset = toolset
        self.ver = ver
        self.year = int(re.sub(r'^vs(....).*', r'\1', name))
        self.gen = __class__.to_gen(cn)
        self.dir = __class__.vsdir(ver)
        self.msbuild = __class__.msbuild(ver)
        self.vcvarsall = __class__.vcvarsall(ver)
        self.is_installed = __class__.is_installed(ver)
        self.cxx_compiler = __class__.cxx_compiler(ver)
        self.c_compiler = __class__.c_compiler(ver)

    def cmd(self, cmd_args, *runsyscmd_args):
        if isinstance(cmd_args, list):
            cmd_args = " ".join(cmd_args)
        cmd_args = self.vcvarsall + "; " + cmd_args
        return runsyscmd(cmd_args, *runsyscmd_args)

    @staticmethod
    def find_any():
        for k in __class__.order:
            if __class__.is_installed(k):
                return __class__(k)
        return None

    @staticmethod
    def cxx_compiler(name_or_gen_or_ver):
        if not __class__.is_installed(name_or_gen_or_ver):
            return None
        return CMakeSysInfo.cxx_compiler(__class__.to_gen(name_or_gen_or_ver))

    @staticmethod
    def c_compiler(name_or_gen_or_ver):
        if not __class__.is_installed(name_or_gen_or_ver):
            return None
        return CMakeSysInfo.c_compiler(__class__.to_gen(name_or_gen_or_ver))

    @staticmethod
    def to_name(name_or_gen_or_ver):
        if isinstance(name_or_gen_or_ver, int):
            return __class__._versions[name_or_gen_or_ver]
        else:
            if name_or_gen_or_ver.startswith('vs'):
                return __class__.sep_name_toolset(name_or_gen_or_ver)[0]
            n = __class__._names.get(name_or_gen_or_ver)
            if n is not None:
                return n
        raise Exception("could not find '{}'".format(name_or_gen_or_ver))

    @staticmethod
    def to_ver(name_or_gen_or_ver):
        if isinstance(name_or_gen_or_ver, int):
            return name_or_gen_or_ver
        else:
            n = __class__.to_name(name_or_gen_or_ver)
            return __class__._versions[n]

    @staticmethod
    def to_gen(name_or_gen_or_ver):
        if isinstance(name_or_gen_or_ver, int):
            name_or_gen_or_ver = __class__._versions[name_or_gen_or_ver]
        if name_or_gen_or_ver.startswith('Visual Studio'):
            return name_or_gen_or_ver
        name_or_gen_or_ver = __class__.sep_name_toolset(name_or_gen_or_ver)[0]
        return __class__._names[name_or_gen_or_ver]

    @staticmethod
    def vsdir(name_or_gen_or_ver):
        """get the directory where VS is installed"""
        ver = __class__.to_ver(name_or_gen_or_ver)
        if ver < 15:
            progfilesx86 = os.environ['ProgramFiles(x86)']
            d = os.path.join(progfilesx86, 'Microsoft Visual Studio ' + str(ver) + '.0')
            if not os.path.exists(d):
                try:
                    v = os.environ['VS{}0COMNTOOLS'.format(str(ver))]
                    d = os.path.abspath(os.path.join(v, '..', '..'))
                except:
                    pass
        elif ver == 15:
            # VS 2017+ is no longer a singleton, and may be installed anywhere,
            # and the environment variable VS***COMNTOOLS no longer exists.
            # So use CMake to do the grunt work for us, and pick up from there.
            # http://stackoverflow.com/questions/40694598/how-do-i-call-visual-studio-2017-rcs-version-of-msbuild-from-a-bat-files
            def fn():
                if not __class__.is_installed(ver):  # but use cmake only if VS2017 is installed
                    return ""
                cxx = CMakeSysInfo.cxx_compiler(__class__.to_gen('vs2017'))
                # VC dir is located on the root of the VS install dir
                vsdir = re.sub(r'(.*)[\\/]VC[\\/].*', r'\1', str(cxx))
                return vsdir
            d = cacheattr(__class__, '_vs2017dir', fn)
        else:
            raise Exception('VS Version not implemented: ' + str(ver))
        return d

    @staticmethod
    def vcvarsall(name_or_gen_or_ver):
        """get the path to vcvarsall.bat"""
        ver = __class__.to_ver(name_or_gen_or_ver)
        if ver < 15:
            s = os.path.join(__class__.vsdir(ver), 'VC', 'vcvarsall.bat')
        elif ver == 15:
            s = os.path.join(__class__.vsdir(ver), 'VC', 'Auxiliary', 'Build', 'vcvarsall.bat')
        else:
            raise Exception('VS Version not implemented: ' + str(ver))
        return s

    @staticmethod
    def msbuild(name_or_gen_or_ver):
        """get the MSBuild.exe path"""
        ver = __class__.to_ver(name_or_gen_or_ver)
        if ver < 15:
            progfilesx86 = os.environ['ProgramFiles(x86)']
            msbuild = os.path.join(progfilesx86, 'MSBuild', str(ver)+'.0', 'bin', 'MSBuild.exe')
        else:
            if ver > 15:
                raise Exception('VS Version not implemented: ' + str(ver))
            if is64:
                msbuild = os.path.join(__class__.vsdir(ver), 'MSBuild', '15.0', 'Bin', 'amd64', 'MSBuild.exe')
            else:
                msbuild = os.path.join(__class__.vsdir(ver), 'MSBuild', '15.0', 'Bin', 'MSBuild.exe')
        return msbuild

    @staticmethod
    def devenv(name_or_gen_or_ver):
        """get path to devenv"""
        raise Exception("not implemented")

    @staticmethod
    def is_installed(name_or_gen_or_ver):
        ver = __class__.to_ver(name_or_gen_or_ver)
        return cacheattr(__class__, '_is_installed_'+str(ver), lambda: __class__._is_installed_impl(ver))

    @staticmethod
    def _is_installed_impl(ver):
        assert isinstance(ver, int)
        if ver < 15:
            import winreg as wr
            key = "SOFTWARE\Microsoft\VisualStudio\{}.0"
            try:
                wr.OpenKey(wr.HKEY_LOCAL_MACHINE, key.format(ver), 0, wr.KEY_READ)
                # fail if we can't find the dir
                if not os.path.exists(__class__.vsdir(ver)):
                    return False
                # apparently the dir is not enough, so check also vcvarsall
                if not os.path.exists(__class__.vcvarsall(ver)):
                    return False
                return True
            except:
                return False
        else:
            #
            # ~~~~~~~~~~~~~~ this is fragile.... ~~~~~~~~~~~~~~
            #
            # Unlike earlier versions, VS2017 is no longer a singleton installation.
            # Each VS2017 installed instance keeps a store of its data under
            # %ProgramData%\Microsoft\VisualStudio\Packages\_Instances\<hash>\state.json
            #
            # this info was taken from:
            # http://stackoverflow.com/questions/40694598/how-do-i-call-visual-studio-2017-rcs-version-of-msbuild-from-a-bat-files
            progdata = os.environ['ProgramData']
            instances_dir = os.path.join(progdata, 'Microsoft', 'VisualStudio', 'Packages', '_Instances')
            if not os.path.exists(instances_dir):
                return False
            pat = os.path.join(instances_dir, '*', 'state.json')
            instances = glob.glob(pat)
            if not instances:
                return False
            for i in instances:
                with open(i, encoding="utf8") as json_str:
                    d = json.load(json_str)
                    # check that the version matches
                    version_string = nested_lookup(d, 'catalogInfo', 'buildVersion')
                    version_number = int(re.sub(r'(\d\d).*', r'\1', version_string))
                    if version_number != ver:
                        continue
                    # check that the directory exists
                    install_dir = nested_lookup(d, 'installationPath')
                    if not os.path.exists(install_dir):
                        continue
                    # maybe further checks are necessary?
                    # For now we stop here, and accept that this installation exists.
                    return True
            return False

