from __future__ import print_function, unicode_literals

import errno
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile


# From https://stackoverflow.com/a/19445241/262432
if sys.platform in ["cygwin", "win32"]:
    _bltn_open = tarfile.bltn_open

    def long_bltn_open(name, *args, **kwargs):
        # http://msdn.microsoft.com/en-us/library/aa365247%28v=vs.85%29.aspx#maxpath
        if len(name) >= 200:
            if not os.path.isabs(name):
                name = os.path.join(os.getcwd(), name)
            name = "\\\\?\\" + os.path.normpath(name)
        return _bltn_open(name, *args, **kwargs)

    tarfile.bltn_open = long_bltn_open


def sed_inplace(path, pattern, sub):
    """Replaces all occurences of ``pattern`` in a file with ``sub``.

    A file is modified **in-place**.
    """
    print("s/{}/{}/ in file {}".format(pattern, sub, path))
    with open(path, "r") as input:
        with tempfile.NamedTemporaryFile("w", delete=False) as output:
            for line in input:
                output.write(line.replace(pattern, sub))

        shutil.copyfile(output.name, path)


def run(command, **kwargs):
    print(command)
    subprocess.check_call(command, shell=True, **kwargs)


def maybe_makedirs(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
