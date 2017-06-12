from __future__ import print_function, unicode_literals

import errno
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from contextlib import contextmanager


# From https://stackoverflow.com/a/19445241/262432
if sys.platform in ["cygwin", "win32"]:
    _bltn_open = tarfile.bltn_open

    def safe_path(path):
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        # http://msdn.microsoft.com/en-us/library/aa365247%28v=vs.85%29.aspx#maxpath
        if len(path) >= 200:
            path = "\\\\?\\" + os.path.normpath(path)
        return path

    def long_bltn_open(name, *args, **kwargs):
        return _bltn_open(safe_path(name), *args, **kwargs)

    tarfile.bltn_open = long_bltn_open


@contextmanager
def cd(path):
    cwd = os.getcwd()
    os.chdir(path)
    print("cd " + path)
    try:
        yield path
    finally:
        os.chdir(cwd)


def sed_inplace(path, pattern, sub, regex=False):
    """Replaces all occurences of ``pattern`` in a file with ``sub``.

    A file is modified **in-place**.
    """
    print("s/{}/{}/ in file {}".format(pattern, sub, path))
    with open(path, "r") as input:
        with tempfile.NamedTemporaryFile("w", delete=False) as output:
            for line in input:
                output.write(line.replace(pattern, sub) if not regex else
                             re.sub(pattern, sub, line))

        shutil.copyfile(output.name, path)


def run(command, **kwargs):
    print(command)
    return subprocess.check_call(command, shell=True, **kwargs)


def maybe_makedirs(path):
    print("mkdir -p " + path)
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
