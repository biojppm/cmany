from collections import OrderedDict as odict
from ruamel import yaml
import copy

from .named_item import NamedItem
from . import util


def get_name_for_flags(compiler):
    if isinstance(compiler, str):
        return compiler
    sn = compiler.name_for_flags
    if compiler.is_msvc:
        if compiler.vs.is_clang:
            sn = 'clang'
        else:
            sn = 'vs'
    return sn


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class FlagAliases:

    def __init__(self, **kwargs):
        if kwargs.get('yml') is not None:
            self.compilers, self.flags = load_yml(kwargs.get('yml'))
        else:
            self.flags = odict(**kwargs)
            self.compilers = get_all_compilers(self.flags)

    def merge_from(self, other):
        self.flags = merge(self.flags, other)
        self.compilers = get_all_compilers(self.flags)

    def get(self, name, compiler=None):
        opt = self.flags.get(name)
        if opt is None:
            raise Exception("could not find flag alias: " + name)
        if compiler is not None:
            return opt.get(compiler)
        return opt

    def as_flags(self, spec, compiler=None):
        out = []
        for s in spec:
            if isinstance(s, CFlag):
                out.append(s)
            else:
                f = self.flags.get(s)
                if f is not None:
                    out.append(f)
                else:
                    ft = CFlag(name=s, desc=s)
                    ft.set(compiler, s)
                    out.append(ft)
        if compiler is not None:
            out = [f.get(compiler) for f in out]
        return out

    def as_defines(self, spec, compiler=None):
        out = []
        wf = '/D' if get_name_for_flags(compiler) == 'vs' else '-D'
        prev = None
        for s in spec:
            if prev != wf and not s.startswith(wf):
                out.append(wf)
            out.append(s)
            prev = s
        return out


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class CFlag(NamedItem):

    def __init__(self, name, desc='', **kwargs):
        super().__init__(name)
        self.desc = desc
        self.compilers = []
        for k, v in kwargs.items():
            self.set(k, v)

    def get(self, compiler):
        compseq = (compiler, 'gcc', 'g++', 'vs')  # not really sure about this
        s = None
        for c in compseq:
            sn = get_name_for_flags(c)
            if hasattr(self, sn):
                s = getattr(self, sn)
                break
        if s is None:
            util.logwarn('compiler not found: ', compiler, self.__dict__)
            s = ''
        # print(self, sn, s)
        return s

    def set(self, compiler, val=''):
        sn = get_name_for_flags(compiler)
        setattr(self, sn, val)
        if sn not in self.compilers:
            self.compilers.append(sn)

    def add_compiler(self, compiler):
        sn = get_name_for_flags(compiler)
        if not hasattr(self, sn):
            self.set(sn)
        if sn not in self.compilers:
            self.compilers.append(sn)

    def merge_from(self, that):
        for k, v in that.__dict__.items():
            if not __class__.is_compiler_name(k):
                continue
            v = that.get(k)
            self.set(k, v)

    @staticmethod
    def is_compiler_name(s):
        return not (s.startswith('__') or s == 'name' or s == 'desc'
                    or s == 'compilers')


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
def dump_yml(comps, flags):
    """dump the given compilers and flags pair into a yml string"""
    txt = ""
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
    dump = list(yaml.load_all(txt, yaml.RoundTripLoader))
    if len(dump) != 1:
        raise Exception('The flags must be in one yaml document. len='
                        + str(len(dump)) + "\n" + str(dump))
    fd = odict(dump[0])
    # gather the list of compilers
    comps = []
    for n, yf in fd.items():
        for c in yf:
            c = str(c)
            if CFlag.is_compiler_name(c):
                for cc in c.split(','):
                    if cc not in comps:
                        comps.append(cc)
    # now load flags, making sure that all have the same compiler names
    flags = odict()
    for n, yf in fd.items():
        f = CFlag(n)
        for c in comps:
            f.add_compiler(c)
        for comp_, val in yf.items():
            for comp in comp_.split(','):
                if comp == 'desc':
                    f.desc = val
                else:
                    f.set(comp, val)
                #print("load yml: flag value for", comp, ":", val, "--------->", f.get(comp))
        flags[n] = f
    return comps, flags


def merge(flags, into_flags=None):
    """merge flags into the previously existing flags"""
    into_flags = into_flags if into_flags is not None else known_flags
    result_flags = into_flags
    comps = get_all_compilers(flags, into_flags)
    result_flags = copy.deepcopy(into_flags)
    for k, v in flags.items():
        if k in result_flags:
            result_flags[k].merge_from(v)
        else:
            result_flags[k] = copy.deepcopy(v)
    for f in result_flags:
        for c in comps:
            result_flags[k].add_compiler(c)
    return result_flags


def get_all_compilers(*flag_dicts):
    comps = []
    for f in flag_dicts:
        for k, v in f.items():
            for c in v.compilers:
                if c not in comps:
                    comps.append(c)
    return comps
