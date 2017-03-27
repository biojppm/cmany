from collections import OrderedDict as odict
from ruamel import yaml
import copy

from . import conf


def _getrealsn(compiler):
    if isinstance(compiler, str):
        return compiler
    sn = compiler.shortname
    if compiler.is_msvc:
        if compiler.vs.is_clang:
            sn = 'clang'
        else:
            sn = 'vs'
    return sn


class CFlag:

    def __init__(self, name, desc='', **kwargs):
        self.name = name
        self.desc = desc
        self.compilers = kwargs.get('compilers', [])
        for k, v in kwargs.items():
            self.set(k, v)

    def get(self, compiler):
        sn = _getrealsn(compiler)
        if hasattr(self, sn):
            s = getattr(self, sn)
        else:
            s = ''
        # print(self, sn, s)
        return s

    def set(self, compiler, val=''):
        sn = _getrealsn(compiler)
        if not sn in self.compilers:
            self.compilers.append(sn)
        setattr(self, sn, val)

    def add_compiler(self, compiler):
        sn = _getrealsn(compiler)
        if not sn in self.compilers:
            self.compilers.append(sn)
        if not hasattr(self, sn):
            self.set(sn)

    def merge_from(self, that):
        for c in that.compilers:
            v = that.get(c)
            self.set(c, v)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


def get(name, compiler=None):
    opt = known_flags.get(name)
    if opt is None:
        raise Exception("could not find compile option preset: " + name)
    if compiler is not None:
        return opt.get(compiler)
    return opt


def as_flags(spec, compiler=None):
    out = []
    for s in spec:
        f = known_flags.get(s)
        if f is not None:
            out.append(f)
        else:
            ft = CFlag(name=s, desc=s)
            ft.set(compiler, s)
            out.append(ft)
    return out


def as_defines(spec, compiler=None):
    out = []
    wf = '/D' if _getrealsn(compiler) == 'vs' else '-D'
    for s in spec:
        out.append(wf)
        out.append(s)
    return out


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
def dump_yml(comps, flags):
    """dump the given compilers and flags pair into a yml string"""
    txt = ""
    txt += 'compilers: ' + yaml.dump(comps)
    txt += '---\n'
    for n, f in flags.items():
        txt += n + ':\n'
        if f.desc:
            txt += '    desc: ' + f.desc + '\n'
        # join equal flag values into comma-separated keys:
        # eg compiler1,compiler2,compiler3: flag value
        rd = odict()
        dr = odict()
        done = odict()
        # store reverse information: flag: compiler1,compiler2,compiler3
        for comp in comps:
            v = getattr(f, comp)
            if not rd.get(v):
                rd[v] = ''
            else:
                rd[v] += ','
            rd[v] += comp
            dr[comp] = v
        # make sure compilers are not repeated
        for comp in comps:
            done[comp] = False
        # now lookup, write and mark
        for comp in comps:
            if done[comp]:
                continue
            val = dr[comp]
            key = rd[val]
            if val:
                txt += '    ' + key + ': ' + val + '\n'
            for ccomp in key.split(','):
                done[ccomp] = True
    return txt


def load_yml(txt):
    """load a yml txt into a compilers, flags pair"""
    comps = []
    flags = odict()
    dump = list(yaml.load_all(txt, yaml.RoundTripLoader))
    if len(dump) != 2:
        msg = 'There must be two yaml documents. Did you forget to use --- to separate the compiler list from the flags?'
        raise Exception(msg)
    comps, fs = dump
    comps = list(comps['compilers'])
    #print("load yml: compilers=", comps)
    flags0 = odict(fs)
    for n, yf in flags0.items():
        f = CFlag(n)
        for c in comps:
            f.add_compiler(c)
        #print("load yml: flag compilers=", f.compilers)
        for comp_, val in yf.items():
            for comp in comp_.split(','):
                if comp == 'desc':
                    f.desc = val
                else:
                    f.set(comp, val)
                #print("load yml: flag value for", comp, ":", val, "--------->", f.get(comp))
        flags[n] = f
    return comps, flags


def save(comps, flags, filename):
    """save the given compilers and flags into a yml file"""
    yml = dump_yml(comps, flags)
    with open(filename, 'w') as f:
        f.write(yml)


def load(filename):
    with open(filename, 'r') as f:
        txt = f.read()
        comps, flags = load_yml(txt)
        return comps, flags


def merge(comps=None, flags=None, into_comps=None, into_flags=None):
    """merge a compilers and flags pair into a previously existing compilers and flags pair"""
    into_comps = into_comps if into_comps is not None else known_compilers
    into_flags = into_flags if into_flags is not None else known_flags
    result_comps = into_comps
    result_flags = into_flags
    if comps:
        result_comps = copy.deepcopy(into_comps)
        for c in comps:
            if not c in into_comps:
                result_comps.append(c)
    if flags:
        result_flags = copy.deepcopy(into_flags)
        for k, v in flags.items():
            if k in result_flags:
                result_flags[k].merge_from(v)
            else:
                result_flags[k] = copy.deepcopy(v)
                for c in result_comps:
                    result_flags[k].add_compiler(c)
    return result_comps, result_flags


def load_and_merge(filename, into_comps=None, into_flags=None):
    comps, flags = load(filename)
    return merge(comps, flags, into_comps, into_flags)


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
known_compilers = []
known_flags = odict()

def load_known_flags(additional_flag_files=[], read_defaults=True):
    """reads first the cmany's known flags file, then the user's
    known flags file, then the given flag files first to last.
    Flags given in latter files will prevail over those of earlier files."""
    import os.path
    global known_compilers, known_flags
    comps = known_compilers if read_defaults else []
    flags = known_flags if read_defaults else odict()
    filenames = [conf.KNOWN_FLAGS_FILE, conf.USER_FLAGS_FILE] if read_defaults else []
    filenames += additional_flag_files
    for f in filenames:
        if os.path.exists(f):
            c, f = load(conf.KNOWN_FLAGS_FILE)
            comps, flags = merge(c, f, comps, flags)
    known_compilers, known_flags = comps, flags
    #for _, v in known_flags.items():
    #    print(v, v.desc, v.gcc, v.vs)
