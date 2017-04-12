#!/usr/bin/env python3

import os
import re
import sys
import subprocess
import platform
import collections
import copy

import colorama #from colorama import Fore, Back, Style, init
colorama.init()


def supports_color():
    """
    Returns True if the running system's terminal supports color, and False
    otherwise.
    Taken from http://stackoverflow.com/questions/7445658/
    """
    plat = sys.platform
    supported_platform = plat != 'Pocket PC' and (plat != 'win32' or
                                                  'ANSICON' in os.environ)
    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    if not supported_platform or not is_a_tty:
        return False
    return True
    # also this: https://gist.github.com/ssbarnea/1316877

cmany_colored_output = supports_color()


def color_log(style, *args, **kwargs):
    if cmany_colored_output:
        print(style, sep='', end='')
        print(*args, **kwargs)
        print(colorama.Style.RESET_ALL, sep='', end='')
    else:
        print(*args, **kwargs)


def loginfo(*args, **kwargs):
    color_log(colorama.Fore.CYAN + colorama.Style.BRIGHT, *args, **kwargs)


def lognotice(*args, **kwargs):
    color_log(colorama.Fore.BLUE + colorama.Style.BRIGHT, *args, **kwargs)


def logdone(*args, **kwargs):
    color_log(colorama.Fore.GREEN + colorama.Style.BRIGHT, *args, **kwargs)


def logwarn(*args, **kwargs):
    color_log(colorama.Fore.YELLOW + colorama.Style.BRIGHT, *args, **kwargs)


def logerr(*args, **kwargs):
    color_log(colorama.Fore.RED + colorama.Style.BRIGHT, *args, **kwargs)


def logcmd(*args, **kwargs):
    #print(*args, **kwargs)
    print("--------")
    color_log(colorama.Fore.WHITE + colorama.Style.BRIGHT, *args, **kwargs)
    # this print here is needed to prevent the command output
    # from being colored. Need to address this somehow.
    print("--------")


#------------------------------------------------------------------------------
def sys_str():
    if sys.platform == "linux" or sys.platform == "linux2":
        return "linux"
    elif sys.platform == "darwin":
        return "mac"
    elif sys.platform == "win32":
        return "windows"
    else:
        raise Exception("unknown system")


def in_windows():
    return sys.platform == "win32"


def in_unix():
    return sys.platform in ("linux", "linux2", "darwin")


def set_executable(filename):
    import stat
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | stat.S_IEXEC)
    # if in_unix():
    #     with open(n[0], 'r') as f:
    #        mode = os.fstat(f.fileno()).st_mode
    #         mode |= 0o111
    #         os.fchmod(f.fileno(), mode & 0o7777)
    # elif in_windows():
    #     import stat
    #     st = os.stat('somefile')
    #     os.chmod('somefile', st.st_mode | stat.S_IEXEC)


def in_64bit():
    """return True if in a 64-bit architecture"""
    # http://stackoverflow.com/a/12578715/5875572
    machine = platform.machine()
    if machine.endswith('64'):
        return True
    elif machine.endswith('86'):
        return False
    raise Exception("unknown platform architecture")
    # return (struct.calcsize('P') * 8) == 64


def in_32bit():
    """return True if in a 32-bit architecture"""
    # http://stackoverflow.com/a/12578715/5875572
    machine = platform.machine()
    if machine.endswith('64'):
        return False
    elif machine.endswith('86'):
        return True
    raise Exception("unknown platform architecture")
    # return (struct.calcsize('P') * 8) == 32


def is_quoted(s):
    if s is None or len(s) == 0:
        return False
    if not (s[0] in "'\"" and s[-1] == s[0]):
        return False
    # At this point we know the string starts and ends
    # with matching quotes. But we don't know if the last quote
    # closes the first one.
    level = 0
    open  = False
    for i, c in enumerate(s):
        is_escaped = i > 0 and s[i - 1] == '\\'
        if c == s[0] and not is_escaped:
            if open:
                level -= 1
                if level == 0 and i != (len(s) - 1):
                    return False
            else:
                level += 1
            open = not open
    return (level == 0)


def has_interior_quotes(s, sep=','):
    q = '[{}{}]'.format('"', "'")
    rxc = '{}{}{}'.format(q, sep, q)  # matches "," ',' ",' ',"
    rxl = '{}{}'.format(q, sep)       # matches ', ",
    rxr = '{}{}'.format(sep, q)       # matches ,' ,"
    got_em = False
    got_em = got_em or (re.search(rxc, s) is not None)
    got_em = got_em or (re.search(rxl, s) is not None)
    got_em = got_em or (re.search(rxr, s) is not None)
    return got_em


def unquote(s):
    if is_quoted(s):
        s = s[1:-1]
    return s


def splitesc_quoted(string, split_char, escape_char='\\', quote_chars='\'"'):
    """split a string at split_char, but respect (and preserve) all the
    characters inside a quote_chars pair (including escaped quote_chars and
    split_chars). split_char can also be escaped when outside of a
    quote_chars pair."""
    out = []
    i = 0
    l = len(string)
    prev = 0
    while i < l:
        is_escaped = (i > 0 and string[i - 1] == escape_char)
        c = string[i]
        # consume at once everything between quotes
        if c in quote_chars:
            j = i+1  # start counting only on the next position
            closes_quotes = False
            while j < l:
                d = string[j]
                is_escaped_j = (j > 0 and string[j - 1] == escape_char)
                if d == c and not is_escaped_j:  # found the matching quote
                    j += 1
                    closes_quotes = True
                    break
                j += 1
            # but defend against unbalanced quotes,
            # treating them as regular characters
            if not closes_quotes:
                i += 1
            else:
                s = string[prev:j]
                if s:
                    out.append(s)
                prev = j+1
                i = prev
        # when a split_char is found, append to the list
        elif c == split_char and not is_escaped:
            if i > 0 and i < l and i > prev:
                s = string[prev:i]
                if s:
                    out.append(s)
            prev = i+1
            i += 1
        # this is a regular character, just go on scanning
        else:
            i += 1
    # if there are still unread characters, append them as well
    if prev < l:
        s = string[prev:l]
        if s:
            out.append(s)
    return out


def splitesc(string, split_char, escape_char=r'\\'):
    """split a string at the given character, allowing for escaped characters
    http://stackoverflow.com/a/21107911"""
    rx = r'(?<!{}){}'.format(escape_char, split_char)
    s = re.split(rx, string)
    return s


def cslist(arg):
    """transform comma-separated arguments into a list of strings.
    commas can be escaped with backslash, \\"""
    s = splitesc(arg, ',')
    l = []
    for elm in s:
        elm = re.sub(r'\\,', r',', elm)
        l.append(elm)
    return l


def intersperse_l(delimiter, iterable):
    """put the delimiter on the left of every element of iterable"""
    it = iter(iterable)
    for x in it:
        yield delimiter
        yield x


def intersperse_r(delimiter, iterable):
    """put the delimiter on the right of every element of iterable"""
    it = iter(iterable)
    for x in it:
        yield x
        yield delimiter


def chkf(*args):
    """join the args as a path and check whether that path exists"""
    f = os.path.join(*args)
    if not os.path.exists(f):
        raise Exception("path does not exist: " + f + ". Current dir=" + os.getcwd())  # nopep8
    return f


def touch(fname, times=None):
    """change the modification and access times of a file.
    http://stackoverflow.com/questions/1158076/implement-touch-using-python
    """
    with open(fname, 'a'):
        os.utime(fname, times)


def remove_if(fname):
    """remove a file if it exists"""
    if os.path.exists(fname):
        os.remove(fname)


def which(cmd):
    """look for an executable in the current PATH environment variable"""
    if exists_and_exec(cmd):
        return cmd
    exts = ("", ".exe", ".bat") if sys.platform == "win32" else [""]
    for path in os.environ["PATH"].split(os.pathsep):
        for e in exts:
            j = os.path.join(path, cmd+e)
            if exists_and_exec(j):
                return j
    return None


def exists_and_exec(file):
    """return true if the given file exists and is executable"""
    if not os.path.exists(file):
        return False
    if not os.access(file, os.R_OK):
        return False
    if not os.access(file, os.X_OK):
        return False
    return True


def cacheattr(obj, name, function):
    """add and cache an object member which is the result of a given function.
    This is for implementing lazy getters when the function call is expensive."""
    if hasattr(obj, name):
        val = getattr(obj, name)
    else:
        val = function()
        setattr(obj, name, val)
    return val


def ctor(cls, args):
    if not isinstance(args, list):
        args = [args]
    l = []
    for i in args:
        l.append(cls(i))
    return l


# -----------------------------------------------------------------------------
def nested_lookup(dictionary, *entry):
    """get a nested entry from a dictionary"""
    try:
        if isinstance(entry, str):
            v = dictionary[entry]
        else:
            v = None
            for e in entry:
                # print("key:", e, "value:", v if v is not None else "<none yet>")
                v = v[e] if v is not None else dictionary[e]
    except:
        raise Exception("could not find entry '" +
                        "/".join(list(entry)) + "' in the dictionary")
    return v


def nested_merge(into_dct, from_dct, into_dct_is_const=True):
    """ adapted from Copied from https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
    """
    out = copy.deepcopy(into_dct) if into_dct_is_const else into_dct
    for k, v in from_dct.items():
        if (k in out and isinstance(out[k], collections.Mapping)
                and isinstance(from_dct[k], collections.Mapping)):
            nested_merge(out[k], from_dct[k], False)
        else:
            out[k] = from_dct[k]
    return out


# -----------------------------------------------------------------------------
class setcwd:
    """temporarily change into a directory inside a with block"""

    def __init__(self, dir_, silent=True):
        self.dir = dir_
        self.silent = silent

    def __enter__(self):
        self.old = os.getcwd()
        if self.old == self.dir:
            return
        if not self.silent:
            print("Entering directory", self.dir, "(was in {})".format(self.old))
        chkf(self.dir)
        os.chdir(self.dir)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.old == self.dir:
            return
        if not self.silent:
            print("Returning to directory", self.old, "(currently in {})".format(self.dir))
        chkf(self.old)
        os.chdir(self.old)

# -----------------------------------------------------------------------------


# subprocess.run() was introduced only in Python 3.5,
# so we provide a replacement implementation to use in older Python versions.
# See http://stackoverflow.com/a/40590445
if sys.version_info >= (3, 5):
    sprun = subprocess.run
else:


    if sys.version_info < (3, 3):
        msg = 'cmany requires at least Python 3.3. Current version is {}. Sorry.'
        sys.exit(msg.format(sys.version_info))


    class CompletedProcess:
        def __init__(self, returncode, args, stdout, stderr):
            self.args = args
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr
        def check_returncode(self):
            if self.returncode:
                if sys.version_info >= (3, 5):
                    raise subprocess.CalledProcessError(
                        self.returncode, self.args, self.stdout, self.stderr)
                else:
                    out = ""
                    if self.stdout:
                        out += self.stdout
                    if self.stderr:
                        out += self.stderr
                    raise subprocess.CalledProcessError(
                        self.returncode, self.args, out)

    def subprocess_run_impl(*popenargs, input=None, check=False, **kwargs):
        if input is not None:
            if 'stdin' in kwargs:
                raise ValueError('stdin and input arguments may not both be used.')
            kwargs['stdin'] = subprocess.PIPE
        process = subprocess.Popen(*popenargs, **kwargs)
        try:
            stdout, stderr = process.communicate(input)
        except:
            process.kill()
            process.wait()
            raise
        retcode = process.poll()
        if check and retcode:
            raise subprocess.CalledProcessError(
                retcode, process.args, output=stdout, stderr=stderr)
        return CompletedProcess(args=process.args, returncode=retcode,
                                stdout=stdout, stderr=stderr)

    # point sprun to our implementation
    sprun = subprocess_run_impl


def runsyscmd(cmd, echo_cmd=True, echo_output=True, capture_output=False, as_bytes_string=False):
    """run a system command. Note that stderr is interspersed with stdout"""

    if not isinstance(cmd, list):
        raise Exception("the command must be a list with each argument a different element in the list")

    if echo_cmd:
        scmd = cmd
        if not isinstance(cmd, str):
            scmd = ""
            for a in cmd:
                if ' ' in a:
                    if in_windows():
                        a = '"' + a + '"'
                    else:
                        a = re.sub(r' ', r'\\ ', a)
                scmd += " " + a
        logcmd('$' + scmd)

    if as_bytes_string:
        if capture_output:
            result = sprun(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDERR)
            result.check_returncode()
            return result.stdout
        else:
            result = sprun(cmd)
            result.check_returncode()
    else:
        if not echo_output:
            result = sprun(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           universal_newlines=True)
            result.check_returncode()
            if capture_output:
                return str(result.stdout)
        elif echo_output:
            if capture_output:
                result = sprun(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True)
                result.check_returncode()
                return str(result.stdout)
            else:
                result = sprun(cmd, universal_newlines=True)
                result.check_returncode()
