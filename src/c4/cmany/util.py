#!/usr/bin/env python3

import os
import re
import sys
import subprocess


# subprocess.run() was introduced in Python 3.5 http://stackoverflow.com/questions/40590192/getting-an-error-attributeerror-module-object-has-no-attribute-run-while

class runresult:
    def __init__(self, args, retcode, stdout, stderr):
        self.args = args
        self.retcode = retcode
        self.stdout = stdout
        self.stderr = stderr
    def check_returncode(self):
        if self.retcode:
            raise subprocess.CalledProcessError(
                self.retcode, self.args, output=self.stdout, stderr=self.stderr)

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
    return runresult(process.args, retcode, stdout, stderr)


if sys.version_info >= (3,5):
    subprocess_run = subprocess.run
else:
    subprocess_run = subprocess_run_impl


def splitesc(string, split_char, escape_char=r'\\'):
    """split a string at the given character, allowing for escaped characters
    http://stackoverflow.com/a/21107911"""
    rx = r'(?<!{}){}'.format(escape_char, split_char)
    s = re.split(rx, string)
    return s


def cslist(arg):
    '''transform comma-separated arguments into a list of strings.
    commas can be escaped with backslash, \\'''
    return splitesc(arg, ',')


def which(cmd):
    """look for an executable in the current PATH environment variable"""
    if os.path.exists(cmd):
        return cmd
    exts = ("",".exe",".bat") if sys.platform == "win32" else ""
    for path in os.environ["PATH"].split(os.pathsep):
        for e in exts:
            j = os.path.join(path, cmd+e)
            if os.path.exists(j):
                return j
    return None


def chkf(*args):
    """join the args as a path and check whether that path exists"""
    f = os.path.join(*args)
    if not os.path.exists(f):
        raise Exception("path does not exist: " + f + ". Current dir=" + os.getcwd())
    return f


def runsyscmd(arglist, echo_cmd=True, echo_output=True, capture_output=False, as_bytes_string=False):
    """run a system command. Note that stderr is interspersed with stdout"""
    s = " ".join(arglist)
    if echo_cmd:
        print("running command:", s)
    if as_bytes_string:
        assert not echo_output
        result = subprocess_run(arglist, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result.check_returncode()
        if capture_output:
            return str(result.stdout)
    elif not echo_output:
        result = subprocess_run(arglist, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                universal_newlines=True)
        result.check_returncode()
        if capture_output:
            return str(result.stdout)
    elif echo_output:
        # http://stackoverflow.com/a/4417735
        popen = subprocess.Popen(arglist, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 universal_newlines=True)
        out = ""
        for stdout_line in iter(popen.stdout.readline, ""):
            print(stdout_line, end="")
            if capture_output:
                out += stdout_line
        popen.stdout.close()
        return_code = popen.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, s)
        if capture_output:
            return out


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


# -----------------------------------------------------------------------------
class setcwd:
    """temporarily change into a directory inside a with block"""

    def __init__(self, dir_, silent=False):
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
