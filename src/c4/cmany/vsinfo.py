#!/usr/bin/env python3

import os
import re
import glob
import json
import sys

from collections import OrderedDict as odict

from . import util
from .util import runsyscmd, cacheattr, nested_lookup, logdbg
from .cmake import CMakeSysInfo
from .err import VSNotFound


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
        self.devenv = devenv(ver)
        self.vcvarsall = vcvarsall(ver)
        self.is_installed = is_installed(ver)
        self.cxx_compiler = cxx_compiler(ver)
        self.c_compiler = c_compiler(ver)
        if self.toolset is not None:
            self.is_clang = re.search(r'clang', self.toolset) is not None
        else:
            self.is_clang = False
    def runsyscmd(self, cmd, **kwargs):
        """
        vcvarsall.bat usage:
        Syntax:
            vcvarsall.bat [arch] [platform_type] [winsdk_version] [-vcvars_ver=vc_version] [-vcvars_spectre_libs=spectre_mode]
        where :
            [arch]: x86 | amd64 | x86_amd64 | x86_arm | x86_arm64 | amd64_x86 | amd64_arm | amd64_arm64
            [platform_type]: {empty} | store | uwp
            [winsdk_version] : full Windows 10 SDK number (e.g. 10.0.10240.0) or "8.1" to use the Windows 8.1 SDK.
            [vc_version] : {none} for default VS 2017 VC++ compiler toolset |
                           "14.0" for VC++ 2015 Compiler Toolset |
                           "14.1x" for the latest 14.1x.yyyyy toolset installed (e.g. "14.11") |
                           "14.1x.yyyyy" for a specific full version number (e.g. 14.11.25503)
            [spectre_mode] : {none} for default VS 2017 libraries without spectre mitigations |
                             "spectre" for VS 2017 libraries with spectre mitigations
        """
        a = str(self.architecture)
        if "64" in a:
            a = "x64"
        cmd = ["cmd", "/C", "call", self.vcvarsall, a, "8.1", "&"] + cmd
        runsyscmd(cmd, **kwargs)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# vs search order
order = ('vs2019', 'vs2017', 'vs2015', 'vs2013', 'vs2012', 'vs2010',
         #'vs2008', 'vs2005',
      )

def find_any():
    for vs in order:
        logdbg("looking for", vs)
        if is_installed(vs):
            logdbg("looking for", vs, "--- it's installed")
            return VisualStudioInfo(vs)
    return None


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# a reversible dictionary for the VS version numbers
_versions = {
    'vs2019':16, 16:'vs2019', 'vs2019_64':16, 'vs2019_32':16, 'vs2019_arm':16 , 'vs2019_arm32':16, 'vs2019_arm64':16, # nopep8
    'vs2017':15, 15:'vs2017', 'vs2017_64':15, 'vs2017_32':15, 'vs2017_arm':15 ,  # nopep8
    'vs2015':14, 14:'vs2015', 'vs2015_64':14, 'vs2015_32':14, 'vs2015_arm':14 ,  # nopep8
    'vs2013':12, 12:'vs2013', 'vs2013_64':12, 'vs2013_32':12, 'vs2013_arm':12 ,  # nopep8
    'vs2012':11, 11:'vs2012', 'vs2012_64':11, 'vs2012_32':11, 'vs2012_arm':11 ,  # nopep8
    'vs2010':10, 10:'vs2010', 'vs2010_64':10, 'vs2010_32':10, 'vs2010_ia64':10,  # nopep8
    'vs2008':9 , 9 :'vs2008', 'vs2008_64':9 , 'vs2008_32':9 , 'vs2008_ia64':9 ,  # nopep8
    'vs2005':8 , 8 :'vs2005', 'vs2005_64':8 , 'vs2005_32':8 ,   # nopep8
}


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if util.in_64bit():
    _sfx = ' Win64'  # suffix
    _arc = 'x64'  # suffix for vs2019
    _arc2 = 'x86_64'
else:
    _sfx = ''  # suffix
    _arc = 'Win32'  # suffix for vs2019
    _arc2 = 'x86'

# a reversible dictionary for the names
_names = {
    'vs2019'      : ['Visual Studio 16 2019', '-A', _arc   ], 'Visual Studio 16 2019' + _arc : 'vs2019'      ,  # nopep8
    'vs2019_32'   : ['Visual Studio 16 2019', '-A', 'Win32'], 'Visual Studio 16 2019'        : 'vs2019_32'   ,  # nopep8
    'vs2019_64'   : ['Visual Studio 16 2019', '-A', 'x64'  ], 'Visual Studio 16 2019 Win64'  : 'vs2019_64'   ,  # nopep8
    'vs2019_arm'  : ['Visual Studio 16 2019', '-A', 'ARM'  ], 'Visual Studio 16 2019 ARM'    : 'vs2019_arm'  ,  # nopep8
    'vs2019_arm32': ['Visual Studio 16 2019', '-A', 'ARM'  ], 'Visual Studio 16 2019 ARM32'  : 'vs2019_arm32',  # nopep8
    'vs2019_arm64': ['Visual Studio 16 2019', '-A', 'ARM64'], 'Visual Studio 16 2019 ARM64'  : 'vs2019_arm64',  # nopep8
    'vs2017'      : 'Visual Studio 15 2017' + _sfx          , 'Visual Studio 15 2017' + _sfx : 'vs2017'      ,  # nopep8
    'vs2017_32'   : 'Visual Studio 15 2017'                 , 'Visual Studio 15 2017'        : 'vs2017_32'   ,  # nopep8
    'vs2017_64'   : 'Visual Studio 15 2017 Win64'           , 'Visual Studio 15 2017 Win64'  : 'vs2017_64'   ,  # nopep8
    'vs2017_arm'  : 'Visual Studio 15 2017 ARM'             , 'Visual Studio 15 2017 ARM'    : 'vs2017_arm'  ,  # nopep8
    'vs2015'      : 'Visual Studio 14 2015' + _sfx          , 'Visual Studio 14 2015' + _sfx : 'vs2015'      ,  # nopep8
    'vs2015_32'   : 'Visual Studio 14 2015'                 , 'Visual Studio 14 2015'        : 'vs2015_32'   ,  # nopep8
    'vs2015_64'   : 'Visual Studio 14 2015 Win64'           , 'Visual Studio 14 2015 Win64'  : 'vs2015_64'   ,  # nopep8
    'vs2015_arm'  : 'Visual Studio 14 2015 ARM'             , 'Visual Studio 14 2015 ARM'    : 'vs2015_arm'  ,  # nopep8
    'vs2013'      : 'Visual Studio 12 2013' + _sfx          , 'Visual Studio 12 2013' + _sfx : 'vs2013'      ,  # nopep8
    'vs2013_32'   : 'Visual Studio 12 2013'                 , 'Visual Studio 12 2013'        : 'vs2013_32'   ,  # nopep8
    'vs2013_64'   : 'Visual Studio 12 2013 Win64'           , 'Visual Studio 12 2013 Win64'  : 'vs2013_64'   ,  # nopep8
    'vs2013_arm'  : 'Visual Studio 12 2013 ARM'             , 'Visual Studio 12 2013 ARM'    : 'vs2013_arm'  ,  # nopep8
    'vs2012'      : 'Visual Studio 11 2012' + _sfx          , 'Visual Studio 11 2012' + _sfx : 'vs2012'      ,  # nopep8
    'vs2012_32'   : 'Visual Studio 11 2012'                 , 'Visual Studio 11 2012'        : 'vs2012_32'   ,  # nopep8
    'vs2012_64'   : 'Visual Studio 11 2012 Win64'           , 'Visual Studio 11 2012 Win64'  : 'vs2012_64'   ,  # nopep8
    'vs2012_arm'  : 'Visual Studio 11 2012 ARM'             , 'Visual Studio 11 2012 ARM'    : 'vs2012_arm'  ,  # nopep8
    'vs2010'      : 'Visual Studio 10 2010' + _sfx          , 'Visual Studio 10 2010' + _sfx : 'vs2010'      ,  # nopep8
    'vs2010_32'   : 'Visual Studio 10 2010'                 , 'Visual Studio 10 2010'        : 'vs2010_32'   ,  # nopep8
    'vs2010_64'   : 'Visual Studio 10 2010 Win64'           , 'Visual Studio 10 2010 Win64'  : 'vs2010_64'   ,  # nopep8
    'vs2010_ia64' : 'Visual Studio 10 2010 IA64'            , 'Visual Studio 10 2010 IA64'   : 'vs2010_ia64' ,  # nopep8
    'vs2008'      : 'Visual Studio 9 2008' + _sfx           , 'Visual Studio 9 2008' + _sfx  : 'vs2008'      ,  # nopep8
    'vs2008_32'   : 'Visual Studio 9 2008'                  , 'Visual Studio 9 2008'         : 'vs2008_32'   ,  # nopep8
    'vs2008_64'   : 'Visual Studio 9 2008 Win64'            , 'Visual Studio 9 2008 Win64'   : 'vs2008_64'   ,  # nopep8
    'vs2008_ia64' : 'Visual Studio 9 2008 IA64'             , 'Visual Studio 9 2008 IA64'    : 'vs2008_ia64' ,  # nopep8
    'vs2005'      : 'Visual Studio 8 2005' + _sfx           , 'Visual Studio 8 2005' + _sfx  : 'vs2005'      ,  # nopep8
    'vs2005_32'   : 'Visual Studio 8 2005'                  , 'Visual Studio 8 2005'         : 'vs2005_32'   ,  # nopep8
    'vs2005_64'   : 'Visual Studio 8 2005 Win64'            , 'Visual Studio 8 2005 Win64'   : 'vs2005_64'   ,  # nopep8
}

_architectures = {
    'Visual Studio 16 2019'         : 'x86'    ,
    'Visual Studio 16 2019 Win32'   : 'x86'    ,
    'Visual Studio 16 2019 Win64'   : 'x86_64' ,
    'Visual Studio 16 2019 x86'     : 'x86'    ,
    'Visual Studio 16 2019 x64'     : 'x86_64' ,
    'Visual Studio 16 2019 ARM'     : 'arm'    ,
    'Visual Studio 16 2019 ARM32'   : 'arm32'  ,
    'Visual Studio 16 2019 ARM64'   : 'arm64'  ,
    'Visual Studio 16 2019 -A '+_arc: _arc2    ,
    'Visual Studio 16 2019 -A Win32': 'x86'    ,
    'Visual Studio 16 2019 -A Win64': 'x86_64' ,
    'Visual Studio 16 2019 -A x64'  : 'x86_64' ,
    'Visual Studio 16 2019 -A x86'  : 'x86'    ,
    'Visual Studio 16 2019 -A ARM'  : 'arm'    ,
    'Visual Studio 16 2019 -A ARM32': 'arm'    ,
    'Visual Studio 16 2019 -A ARM64': 'arm64'  ,
    'Visual Studio 15 2017'         : 'x86'    ,
    'Visual Studio 15 2017 Win64'   : 'x86_64' ,
    'Visual Studio 15 2017 ARM'     : 'arm'    ,
    'Visual Studio 14 2015'         : 'x86'    ,
    'Visual Studio 14 2015 Win64'   : 'x86_64' ,
    'Visual Studio 14 2015 ARM'     : 'arm'    ,
    'Visual Studio 12 2013'         : 'x86'    ,
    'Visual Studio 12 2013 Win64'   : 'x86_64' ,
    'Visual Studio 12 2013 ARM'     : 'arm'    ,
    'Visual Studio 11 2012'         : 'x86'    ,
    'Visual Studio 11 2012 Win64'   : '_64'    ,
    'Visual Studio 11 2012 ARM'     : 'arm'    ,
    'Visual Studio 10 2010'         : 'x86'    ,
    'Visual Studio 10 2010 Win64'   : 'x86_64' ,
    'Visual Studio 10 2010 IA64'    : 'ia64'   ,
    'Visual Studio 9 2008'          : 'x86'    ,
    'Visual Studio 9 2008 Win64'    : 'x86_64' ,
    'Visual Studio 9 2008 IA64'     : 'ia64'   ,
    'Visual Studio 8 2005'          : 'x86'    ,
    'Visual Studio 8 2005 Win64'    : 'x86_64' ,
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
    raise Exception(f"could not find '{name_or_gen_or_ver}'")


def to_ver(name_or_gen_or_ver):
    if isinstance(name_or_gen_or_ver, int):
        return name_or_gen_or_ver
    else:
        n = to_name(name_or_gen_or_ver)
        return _versions[n]


def to_gen(name_or_gen_or_ver):
    n = name_or_gen_or_ver
    if isinstance(n, int):
        n = _versions[n]
    elif isinstance(n, str):
        if n.startswith('Visual Studio'):
            return name_or_gen_or_ver
    elif isinstance(n, list):
        return n
    n = sep_name_toolset(n)[0]
    return _names[n]


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

_toolsets = (
    # vs2019 compiler toolsets
    'v142_clang_c2', 'v142_clang', 'v142_xp', 'v142',
    # vs2017 compiler toolsets
    'v141_clang_c2', 'v141_clang', 'v141_xp', 'v141',
    # vs2015 compiler toolsets
    'v140_clang_c2', 'v140_clang', 'v140_xp', 'v140',
    # vs2013 compiler toolsets
    'v120_xp', 'v120',
    # vs2012 compiler toolsets
    'v110_xp', 'v110',
    # vs2010 compiler toolsets
    'v100_xp', 'v100',
    # vs2008 compiler toolsets
    'v90_xp', 'v90',
    # vs2005 compiler toolsets
    'v80',
    # aliases - implicit compiler toolsets (the same as the chosen VS version)
    'clang_c2', 'clang', 'xp',
)
_toolsets_for_re = sorted(_toolsets, key=lambda x: -len(x))


def sep_name_toolset(name, canonize=True):
    """separate name and toolset"""
    toolset = None
    if isinstance(name, str):
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
        if year == 2019:
            vs_toolset = 'v142_' + toolset
        elif year == 2017:
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
            elif year == 2008:
                vs_toolset = 'v90_' + toolset
            elif year == 2005:
                vs_toolset = 'v80_' + toolset
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
    if isinstance(gen, list):
        gen = " ".join(gen)
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
            except Exception as e:
                pass
        return d
    #
    # VS 2017+ is no longer a singleton, and may be installed anywhere;
    # also, the environment variable VS***COMNTOOLS no longer exists.
    def fn_201x():
        try:
            idata = _vs201x_get_instance(ver)
            path = idata.install_dir()
            logdbg("install dir:", ver, "---", idata, path)
            return path
        except Exception as e:
            return ""
    if ver == 15:
        d = cacheattr(sys.modules[__name__], '_vs2017dir', lambda: fn_201x())
    elif ver == 16:
        d = cacheattr(sys.modules[__name__], '_vs2019dir', lambda: fn_201x())
    else:
        raise Exception('VS Version not implemented: ' + str(ver))
    return d


def devenv(name_or_gen_or_ver):
    """get the path to devenv.exe"""
    ver = to_ver(name_or_gen_or_ver)
    d = vsdir(ver)
    # devenv can have different names:
    # see http://stackoverflow.com/questions/7818543/no-devenv-file-in-microsoft-visual-express-10
    for n in ('devenv.exe', 'WDExpress.exe', 'VSWinExpress.exe'):
        s = os.path.join(d, 'Common7', 'IDE', n)
        if os.path.exists(s):
            return s
    return None


def vcvarsall(name_or_gen_or_ver):
    """get the path to vcvarsall.bat"""
    ver = to_ver(name_or_gen_or_ver)
    d = vsdir(ver)
    if ver < 15:
        s = os.path.join(d, 'VC', 'vcvarsall.bat')
    elif ver == 15 or ver == 16:
        s = os.path.join(d, 'VC', 'Auxiliary', 'Build', 'vcvarsall.bat')
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
                val = wr.OpenKey(wr.HKEY_LOCAL_MACHINE, key.format(v), 0, wr.KEY_READ)
                msbuild = os.path.join(val, 'MSBuild.exe')
                break
            except Exception as e:
                pass
        # default to some probable value if no registry key was found
        if msbuild is None:
            val = 'C:\\Windows\Microsoft.NET\Framework{}\\v{}\\MSBuild.exe'
            for v in msbvers:
                msbuild = val.format('64' if util.in_64bit() else '', v)#'3.5')
                if os.path.exists(msbuild):
                    break
    elif ver < 15:
        root = os.environ['ProgramFiles(x86)']
        val = '{}\\MSBuild\\{}.0\\bin\\{}MSBuild.exe'
        msbuild = val.format(root, ver, 'amd64\\' if util.in_64bit() else '')
    elif ver == 15:
        root = vsdir(ver)
        val = '{}\\MSBuild\\{}.0\\bin\\{}MSBuild.exe'
        msbuild = val.format(root, ver, 'amd64\\' if util.in_64bit() else '')
    elif ver == 16:
        # https://developercommunity.visualstudio.com/content/problem/400763/incorrect-path-to-msbuild-160-vs-2019-preview-1.html
        root = vsdir(ver)
        val = '{}\\MSBuild\\Current\\bin\\{}MSBuild.exe'
        msbuild = val.format(root, 'amd64\\' if util.in_64bit() else '')
    else:
        raise Exception("VS Version not implemented: " + str(ver))
    return msbuild


def cxx_compiler(name_or_gen_or_ver):
    if not is_installed(name_or_gen_or_ver):
        return ""
    return CMakeSysInfo.cxx_compiler(to_gen(name_or_gen_or_ver))


def c_compiler(name_or_gen_or_ver):
    if not is_installed(name_or_gen_or_ver):
        return ""
    return CMakeSysInfo.c_compiler(to_gen(name_or_gen_or_ver))


def is_installed(name_or_gen_or_ver):
    logdbg("is installed?", name_or_gen_or_ver)
    ver = to_ver(name_or_gen_or_ver)
    logdbg("is installed? ver=", name_or_gen_or_ver)
    return cacheattr(sys.modules[__name__], '_is_installed_'+str(ver), lambda: _is_installed_impl(ver))


def _is_installed_impl(ver):
    logdbg("_is_installed_impl:", ver)
    assert isinstance(ver, int)
    if ver < 15:
        #import winreg as wr
        #key = "SOFTWARE\\Microsoft\\VisualStudio\\{}.0"
        try:
            #wr.OpenKey(wr.HKEY_LOCAL_MACHINE, key.format(ver), 0, wr.KEY_READ)
            logdbg("_is_installed_impl:", ver, "--- old stile")
            # fail if we can't find the dir
            if not os.path.exists(vsdir(ver)):
                logdbg("_is_installed_impl:", ver, "--- vsdir does not exist")
                return False
            # apparently the dir is not enough, so check also vcvarsall
            if not os.path.exists(vcvarsall(ver)):
                logdbg("_is_installed_impl:", ver, "--- vcvarsall not found")
                return False
            logdbg("_is_installed_impl:", ver, "--- vcvarsall not found")
            return True
        except Exception as e:
            return False
    else:
        #
        # ~~~~~~~~~~~~~~ this is fragile.... ~~~~~~~~~~~~~~
        #
        # Unlike earlier versions, VS2017+ is no longer a singleton installation.
        # Each VS2017+ installed instance keeps a store of its data under
        # %ProgramData%\Microsoft\VisualStudio\Packages\_Instances\<hash>\state.json
        #
        # this info was taken from:
        # http://stackoverflow.com/questions/40694598/how-do-i-call-visual-studio-2017-rcs-version-of-msbuild-from-a-bat-files
        try:
            logdbg("_is_installed_impl:", ver, "--- new stile")
            d = _vs201x_get_instance(ver)
            logdbg("_is_installed_impl:", ver, "--- d=", d)
        except VSNotFound as e:
            logdbg("_is_installed_impl:", ver, "--- instance not found!", e)
            return False
        idir = d.install_dir()
        logdbg("_is_installed_impl:", ver, "--- install dir=", idir)
        if not os.path.exists(idir):
            logdbg("_is_installed_impl:", ver, "--- install dir does not exist!")
            return False
        logdbg("_is_installed_impl:", ver, "--- got it!", d)
        # maybe further checks are necessary?
        # For now we stop here, and accept that this installation exists.
        return True


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


class VSInstanceData:
    __slots__ = ('path', 'name', 'data', 'version')
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(os.path.dirname(path))
        with open(path, encoding="utf8") as json_str:
            self.data = json.load(json_str)
        self.version = self.data['catalogInfo']['buildVersion']
        #self.version_number = int(re.sub(r'(\d\d).*', r'\1', version_string))
    def __str__(self):
        return "{}({})".format(self.name, self.version)
    def is_ver(self, ver):
        return self.version.startswith(str(ver) + ".")
    def lookup(self, *args):
        return nested_lookup(self.data, *args)
    def install_dir(self):
        return nested_lookup(self.data, "installationPath")


def _vs201x_get_instance_data(ver, which_instance=None):
    id = _vs201x_get_instance(ver, which_instance)
    return id.data


def _vs201x_get_instance(ver, which_instance=None):
    assert ver is not None
    assert isinstance(ver, int)
    logdbg("looking for instance:", ver)
    def fn():
        id = _vs201x_resolve_instance(ver, which_instance)
        if id is None:
            if which_instance is not None:
                err = "could not find a vs2017+ instance named '{}' matching version '{}'. valid: {}"
                raise VSNotFound(err.format(which_instance, ver, _vs201x_get_instances()))
            else:
                err = "could not find a vs2017+ instance matching version '{}'. valid: {}"
                raise VSNotFound(err.format(ver, _vs201x_get_instances()))
        return id
    return cacheattr(sys.modules[__name__], "_vs201x_{}_instance_data_".format(ver), fn)


def _vs201x_resolve_instance(ver, which_instance=None):
    progdata = os.environ['ProgramData']
    d = os.path.join(progdata, 'Microsoft', 'VisualStudio', 'Packages', '_Instances')
    instances = _vs201x_get_instances()
    if instances is None:
        raise VSNotFound("could not find a vs201x instance in " + d)
    i = None
    for j in instances.values():
        if ver is not None:
            if j.is_ver(ver):
                return j
            continue
        if (which_instance is None) or (which_instance == j):
            i = j
            break
    return i


def _vs201x_get_instances():
    def fn():
        d = odict()
        progdata = os.environ['ProgramData']
        instances_dir = os.path.join(progdata, 'Microsoft', 'VisualStudio', 'Packages', '_Instances')
        if not os.path.exists(instances_dir):
            return d
        pat = os.path.join(instances_dir, '*', 'state.json')
        instances = glob.glob(pat)
        logdbg("vs: found instances:", instances)
        if not instances:
            return d
        for i in instances:
            id = VSInstanceData(i)
            d[id.name] = id
            logdbg("vs: instance:", id, i)
        return d
    return cacheattr(sys.modules[__name__], "_vs201x_instances", fn)
