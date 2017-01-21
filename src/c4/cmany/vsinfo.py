#!/usr/bin/env python3

import os
import re
import glob
import json
import sys

from collections import OrderedDict as odict

from . import util
from .util import runsyscmd, cacheattr, nested_lookup
from .cmake import CMakeSysInfo


class VisualStudioInfo:
    """encapsulates info on Visual Studio installations"""

    def __init__(self, name):
        cn, toolset = sep_name_toolset(name)
        if cn not in _versions.keys():
            raise Exception("unknown alias: " + name)
        ver = _versions[cn]
        self.name = name
        self.name_without_toolset = cn
        self.toolset = toolset
        self.ver = ver
        self.year = int(re.sub(r'^vs(....).*', r'\1', name))
        self.gen = to_gen(cn)
        self.architecture = parse_architecture(self.gen)
        self.dir = vsdir(ver)
        self.msbuild = msbuild(ver)
        self.vcvarsall = vcvarsall(ver)
        self.is_installed = is_installed(ver)
        self.cxx_compiler = cxx_compiler(ver)
        self.c_compiler = c_compiler(ver)
        if self.toolset is not None:
            self.is_clang = re.search(r'clang', self.toolset) is not None
        else:
            self.is_clang = False

    def cmd(self, cmd_args, *runsyscmd_args):
        if isinstance(cmd_args, list):
            cmd_args = " ".join(cmd_args)
        cmd_args = self.vcvarsall + "; " + cmd_args
        return runsyscmd(cmd_args, *runsyscmd_args)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# vs search order
order = ('vs2015', 'vs2017', 'vs2013', 'vs2012', 'vs2010',
         #'vs2008', 'vs2005',
      )

def find_any():
    for vs in order:
        ver = to_ver(vs)
        if is_installed(vs):
            return VisualStudioInfo(vs)
    return None

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
_sfx = ' Win64' if util.in_64bit() else ''

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
    'vs2008'      : 'Visual Studio 9 2008' + _sfx  , 'Visual Studio 9 2008' + _sfx  : 'vs2008'      ,  # nopep8
    'vs2008_32'   : 'Visual Studio 9 2008'         , 'Visual Studio 9 2008'         : 'vs2008_32'   ,  # nopep8
    'vs2008_64'   : 'Visual Studio 9 2008 Win64'   , 'Visual Studio 9 2008 Win64'   : 'vs2008_64'   ,  # nopep8
    'vs2008_ia64' : 'Visual Studio 9 2008 IA64'    , 'Visual Studio 9 2008 IA64'    : 'vs2008_ia64' ,  # nopep8
    'vs2005'      : 'Visual Studio 8 2005' + _sfx  , 'Visual Studio 8 2005' + _sfx  : 'vs2005'      ,  # nopep8
    'vs2005_32'   : 'Visual Studio 8 2005'         , 'Visual Studio 8 2005'         : 'vs2005_32'   ,  # nopep8
    'vs2005_64'   : 'Visual Studio 8 2005 Win64'   , 'Visual Studio 8 2005 Win64'   : 'vs2005_64'   ,  # nopep8
}

_architectures = {
    'Visual Studio 15 2017'        : 'x86'    ,
    'Visual Studio 15 2017 Win64'  : 'x86_64' ,
    'Visual Studio 15 2017 ARM'    : 'arm'    ,
    'Visual Studio 14 2015'        : 'x86'    ,
    'Visual Studio 14 2015 Win64'  : 'x86_64' ,
    'Visual Studio 14 2015 ARM'    : 'arm'    ,
    'Visual Studio 12 2013'        : 'x86'    ,
    'Visual Studio 12 2013 Win64'  : '_64'    ,
    'Visual Studio 12 2013 ARM'    : 'arm'    ,
    'Visual Studio 11 2012'        : 'x86'    ,
    'Visual Studio 11 2012 Win64'  : '_64'    ,
    'Visual Studio 11 2012 ARM'    : 'arm'    ,
    'Visual Studio 10 2010'        : 'x86'    ,
    'Visual Studio 10 2010 Win64'  : 'x86_64' ,
    'Visual Studio 10 2010 IA64'   : 'ia64'   ,
    'Visual Studio 9 2008'         : 'x86'    ,
    'Visual Studio 9 2008 Win64'   : 'x86_64' ,
    'Visual Studio 9 2008 IA64'    : 'ia64'   ,
    'Visual Studio 8 2005'         : 'x86'    ,
    'Visual Studio 8 2005 Win64'   : 'x86_64' ,
}

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
def to_name(name_or_gen_or_ver):
    if isinstance(name_or_gen_or_ver, int):
        return _versions[name_or_gen_or_ver]
    else:
        if name_or_gen_or_ver.startswith('vs'):
            return sep_name_toolset(name_or_gen_or_ver)[0]
        n = _names.get(name_or_gen_or_ver)
        if n is not None:
            return n
    raise Exception("could not find '{}'".format(name_or_gen_or_ver))


def to_ver(name_or_gen_or_ver):
    if isinstance(name_or_gen_or_ver, int):
        return name_or_gen_or_ver
    else:
        n = to_name(name_or_gen_or_ver)
        return _versions[n]


def to_gen(name_or_gen_or_ver):
    if isinstance(name_or_gen_or_ver, int):
        name_or_gen_or_ver = _versions[name_or_gen_or_ver]
    if name_or_gen_or_ver.startswith('Visual Studio'):
        return name_or_gen_or_ver
    name_or_gen_or_ver = sep_name_toolset(name_or_gen_or_ver)[0]
    return _names[name_or_gen_or_ver]


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

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


def sep_name_toolset(name, canonize=True):
    """separate name and toolset"""
    toolset = None
    for t in _toolsets_for_re:
        rx = r'vs.....*_({})$'.format(t)
        if re.search(rx, name):
            toolset = re.sub(rx, r'\1', name)
            name_without_toolset = re.sub(r'(vs.....*)_({})$'.format(t), r'\1', name)
            break
    if toolset is None:
        return name, None
    if toolset not in _toolsets:
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


def parse_toolset(name, canonize=True):
    _, toolset = sep_name_toolset(name, canonize)
    return toolset


def parse_architecture(name_or_gen_or_ver):
    gen = to_gen(name_or_gen_or_ver)
    a = _architectures[gen]
    return a

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
def vsdir(name_or_gen_or_ver):
    """get the directory where VS is installed"""
    ver = to_ver(name_or_gen_or_ver)
    d = ""
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
        # VS 2017+ is no longer a singleton, and may be installed anywhere;
        # also, the environment variable VS***COMNTOOLS no longer exists.
        def fn():
            try:
                idata = _vs2017_get_instance_data()
                path = nested_lookup(idata, 'installationPath')
                return path
            except:
                return ""
        d = cacheattr(sys.modules[__name__], '_vs2017dir', fn)
    else:
        raise Exception('VS Version not implemented: ' + str(ver))
    return d


def vcvarsall(name_or_gen_or_ver):
    """get the path to vcvarsall.bat"""
    ver = to_ver(name_or_gen_or_ver)
    if ver < 15:
        s = os.path.join(vsdir(ver), 'VC', 'vcvarsall.bat')
    elif ver == 15:
        s = os.path.join(vsdir(ver), 'VC', 'Auxiliary', 'Build', 'vcvarsall.bat')
    else:
        raise Exception('VS Version not implemented: ' + str(ver))
    return s


def msbuild(name_or_gen_or_ver):
    """get the MSBuild.exe path"""
    ver = to_ver(name_or_gen_or_ver)
    if ver < 12:   # VS2012 and below
        import winreg as wr
        msbuild = None
        msbvers = ('4.0', '3.5', '2.0')
        for v in msbvers:
            key = "SOFTWARE\\Microsoft\\MSBuild\\ToolsVersions\\{}\\MS‌​BuildToolsPath"
            try:
                val = wr.OpenKey(wr.HKEY_LOCAL_MACHINE, key.format(ver), 0, wr.KEY_READ)
                msbuild = os.path.join(val, 'MSBuild.exe')
                break
            except:
                pass
        # default to some probable value if no registry key was found
        if msbuild is None:
            val = 'C:\\Windows\Microsoft.NET\Framework{}\\v{}\\MSBuild.exe'
            for v in msbvers:
                msbuild = val.format('64' if util.in_64bit() else '', '3.5')
                if os.path.exists(msbuild):
                    break
    else:
        root = os.environ['ProgramFiles(x86)'] if ver < 15 else vsdir(ver)
        val = '{}\\MSBuild\\{}.0\\bin\\{}MSBuild.exe'
        msbuild = val.format(root, ver, 'amd64\\' if util.in_64bit() else '')
    return msbuild


def devenv(name_or_gen_or_ver):
    """get path to devenv"""
    raise Exception("not implemented")


def cxx_compiler(name_or_gen_or_ver):
    if not is_installed(name_or_gen_or_ver):
        return ""
    return CMakeSysInfo.cxx_compiler(to_gen(name_or_gen_or_ver))


def c_compiler(name_or_gen_or_ver):
    if not is_installed(name_or_gen_or_ver):
        return ""
    return CMakeSysInfo.c_compiler(to_gen(name_or_gen_or_ver))


def is_installed(name_or_gen_or_ver):
    ver = to_ver(name_or_gen_or_ver)
    return cacheattr(sys.modules[__name__], '_is_installed_'+str(ver), lambda: _is_installed_impl(ver))


def _is_installed_impl(ver):
    assert isinstance(ver, int)
    if ver < 15:
        import winreg as wr
        key = "SOFTWARE\\Microsoft\\VisualStudio\\{}.0"
        try:
            wr.OpenKey(wr.HKEY_LOCAL_MACHINE, key.format(ver), 0, wr.KEY_READ)
            # fail if we can't find the dir
            if not os.path.exists(vsdir(ver)):
                return False
            # apparently the dir is not enough, so check also vcvarsall
            if not os.path.exists(vcvarsall(ver)):
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
        for i in iter(_vs2017_get_instances().keys()):
            try:
                d = _vs2017_get_instance_data(i)
            except:
                continue
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


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
def _vs2017_get_instance_data(which_instance=None):
    i = _vs2017_resolve_instance(which_instance)
    if i is None and which_instance is not None:
        err = "could not find a vs2017 instance named {}"
        raise Exception(err.format(which_instance))
    def fn():
        instances = _vs2017_get_instances()
        with open(instances[i], encoding="utf8") as json_str:
            d = json.load(json_str)
            return d
    return cacheattr(sys.modules[__name__], "_vs2017_instance_data_" + i, fn)


def _vs2017_resolve_instance(which_instance=None):
    progdata = os.environ['ProgramData']
    d = os.path.join(progdata, 'Microsoft', 'VisualStudio', 'Packages', '_Instances')
    instances = _vs2017_get_instances()
    if instances is None:
        raise Exception("could not find a vs2017 instance in " + d)
    i = None
    for j in iter(instances.keys()):
        if (which_instance is None) or (which_instance == j):
            i = j
            break
    return i


def _vs2017_get_instances():
    def fn():
        d = odict()
        progdata = os.environ['ProgramData']
        instances_dir = os.path.join(progdata, 'Microsoft', 'VisualStudio', 'Packages', '_Instances')
        if not os.path.exists(instances_dir):
            return d
        pat = os.path.join(instances_dir, '*', 'state.json')
        instances = glob.glob(pat)
        if not instances:
            return d
        for i in instances:
            d[os.path.basename(os.path.dirname(i))] = i
        return d
    return cacheattr(sys.modules[__name__], "_vs2017_instances", fn)
