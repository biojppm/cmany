#!/usr/bin/env python3

import os
import re
import sys
import subprocess
import platform
import copy
import datetime
from dateutil.relativedelta import relativedelta

import colorama #from colorama import Fore, Back, Style, init
colorama.init()

_debug_mode = False


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

_suppress_colors = False
def suppress_colors():
    global _suppress_colors
    _suppress_colors = True

cmany_colored_output = (not _suppress_colors) and supports_color()


def color_log(style, *args, **kwargs):
    if cmany_colored_output:
        print(style, sep='', end='')
        print(*args, **kwargs)
        print(colorama.Style.RESET_ALL, sep='', end='')
    else:
        print(*args, **kwargs)


def logdbg(*args, **kwargs):
    if _debug_mode:
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
    # print(*args, **kwargs)
    print("--------")
    color_log(colorama.Fore.WHITE + colorama.Style.BRIGHT, *args, **kwargs)
    # this print here is needed to prevent the command output
    # from being colored. Need to address this somehow.
    print("--------")


# -----------------------------------------------------------------------------
def human_readable_time(seconds):
    if seconds < 60.:
        return '{:.3g}s'.format(seconds)
    elif seconds < 3600.:
        mins = int(seconds / 60.)
        secs = int(seconds - 60.*mins)
        return '{}m {}s'.format(mins, secs)
    else:
        hours = int(seconds / 3600.)
        mins = int((seconds - hours*3600.)/60.)
        secs = int(seconds - hours*3600. - mins*60.)
        return '{}:{} {}\''.format(hours, mins, secs)


# -----------------------------------------------------------------------------
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
    open = False
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


def splitesc_quoted_first(string, split_char, escape_char='\\', quote_chars='\'"'):
    """like splitesc_quoted(), but split only the first instance"""
    s = splitesc_quoted(string, split_char, escape_char, quote_chars)
    if len(s) <= 1:
        return s
    else:
        r = [s[0], split_char.join(s[1:])]
        return r


def splitesc_quoted(string, split_char, escape_char='\\', quote_chars='\'"'):
    """split a string at split_char, but respect (and preserve) all the
    characters inside a quote_chars pair (including escaped quote_chars and
    split_chars). split_char can also be escaped when outside of a
    quote_chars pair."""
    #
    #def log(*args): print(*args)
    #def logf(fmt, *args): print(fmt.format(*args))
    def _log(*args): pass
    def _logf(fmt, *args): pass
    #
    # lexer = shlex.shlex(string)
    # lexer.quotes = quote_chars
    # lexer.escape = escape_char
    # lexer.whitespace = split_char
    # #lexer.whitespace_split = True
    # li = list(lexer)
    # return li
    out = []
    i = 0
    l = len(string)
    prev = 0
    _log("\n\n\nsplitting:", string)
    while i < l:
        is_escaped = (i > 0 and string[i - 1] == escape_char)
        c = string[i]
        # consume at once everything between quotes
        if c in quote_chars:
            _logf("{}: case 1: got a quote char: {}", i, c)
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
                _logf("{}: case 1.1: quote char is not closed", i)
                i += 1
            else:
                s = string[prev:j]
                _logf("{}: case 1.2: quote char closes at {}: __|{}|__", i, j, s)
                if (j < l and string[j] != split_char):
                    s += string[j]
                    _logf("{}: case 1.2-0: append one char: __|{}|__", i, s)
                if s:
                    if (prev > 0 and string[prev-1] == split_char):
                        prev = j+1
                        i = prev
                        out.append(s)
                        _logf("{}: case 1.2-1.1: added __|{}|__ as last entry: {}", i, s, out)
                    else:
                        prev = j+1
                        i = prev
                        if out:
                            out[-1] += s
                            _logf("{}: case 1.2-2.1: appended to last entry: {}", i, out[-1])
                        else:
                            out.append(s)
                            _logf("{}: case 1.2-2.2: added __|{}|__ as last entry: {}", i, s, out)
        # when a split_char is found, just append to the list
        elif c == split_char and not is_escaped:
            _logf("{}: case 2: got a split char: '{}'", i, c)
            #if i > 0 and i < l and i > prev: # i is > 0 and because of the condition above, is always i<l
            if i > prev:
                s = string[prev:i]
                _logf("{}: case 2.1: s='{}'", i, s)
                if s:
                    out.append(s)
                    _logf("{}: case 2.1-0: appended, out={}", i, out)
            prev = i+1
            i = prev
        # this is a regular character, so just go on scanning
        else:
            i += 1
    # if there are still unread characters, append them as well
    if prev < l:
        s = string[prev:l]
        _logf("there are remaining characters: {}", s)
        if s:
            # if (prev >= 1 and prev < l and string[prev-1] != split_char) and out:
            if (prev >= 1 and string[prev-1] != split_char) and out:  # note that prev<l here because of the test above
                out[-1] += s
                _logf("appended to last entry: {}", out)
            else:
                out.append(s)
                _logf("add __|{}|__ as last entry: {}", s, out)
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


def find_files_with_ext(folder, ext):
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(ext):
                yield os.path.join(root, file)


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
        if (k in out and isinstance(out[k], type(into_dct))
                and isinstance(from_dct[k], type(from_dct))):
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

def time_since_modification(path):
    """return the time elapsed since a path has been last modified, as a
    dateutil.relativedelta"""
    mtime = os.path.getmtime(path)
    mtime = datetime.datetime.fromtimestamp(mtime)
    currt = datetime.datetime.now()
    r = relativedelta(currt, mtime)
    return r


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


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# https://stackoverflow.com/questions/4675728/redirect-stdout-to-a-file-in-python/22434262#22434262

from contextlib import contextmanager


def fileno(file_or_fd):
    fd = getattr(file_or_fd, 'fileno', lambda: file_or_fd)()
    if not isinstance(fd, int):
        raise ValueError("Expected a file (`.fileno()`) or a file descriptor")
    return fd


def merged_stderr_stdout():  # $ exec 2>&1
    return stdout_redirected(to=sys.stdout, stdout=sys.stderr)


@contextmanager
def stdout_redirected(to=os.devnull, stdout=None):
    if stdout is None:
       stdout = sys.stdout
    stdout_fd = fileno(stdout)
    # copy stdout_fd before it is overwritten
    #NOTE: `copied` is inheritable on Windows when duplicating a standard stream
    with os.fdopen(os.dup(stdout_fd), 'wb') as copied:
        stdout.flush()  # flush library buffers that dup2 knows nothing about
        try:
            os.dup2(fileno(to), stdout_fd)  # $ exec >&to
        except ValueError:  # filename
            with open(to, 'wb') as to_file:
                os.dup2(to_file.fileno(), stdout_fd)  # $ exec > to
        try:
            yield stdout # allow code to be run with the redirected stdout
        finally:
            # restore stdout to its previous value
            #NOTE: dup2 makes stdout_fd inheritable unconditionally
            stdout.flush()
            os.dup2(copied.fileno(), stdout_fd)  # $ exec >&copied
