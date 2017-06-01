from __future__ import print_function, unicode_literals

import errno
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, "wb")


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


def install_dependencies():
    if "TRAVIS" in os.environ:
        if os.environ["TRAVIS_OS_NAME"] == "osx":
            run("brew install protobuf@2.5", stdout=open(os.devnull, "wb"))
            os.environ["HADOOP_PROTOC_CDH5_PATH"] = \
                "/usr/local/opt/protobuf@2.5/bin/protoc"

            # TODO: do we need sudo?
            # Make maven-antrun-plugin happy and put tools.jar to the
            # magical place.
            java_home = os.environ["JAVA_HOME"]
            maybe_makedirs(os.path.join(java_home, "Classes"))
            os.link(os.path.join(java_home, "lib", "tools.jar"),
                    os.path.join(java_home, "Classes", "classes.jar"))
    elif "APPVEYOR" in os.environ:
        protobuf_archive, _headers = urlretrieve(
            "https://github.com/google/protobuf/releases/download/"
            "v2.5.0/protoc-2.5.0-win32.zip")
        with zipfile.ZipFile(protobuf_archive, "r") as zf:
            zf.extractall()


if __name__ == "__main__":
    install_dependencies()

    hadoop_dir = "hadoop-" + os.environ["HADOOP_VERSION"]

    if not os.path.exists(hadoop_dir):
        hadoop_archive = hadoop_dir + ".tar.gz"
        print("Downloading " + hadoop_archive)
        urlretrieve("http://archive.cloudera.com/cdh5/cdh/5/" + hadoop_archive,
                    hadoop_archive)
        with tarfile.open(hadoop_archive, "r:gz") as tf:
            tf.extractall()
        assert os.path.exists(hadoop_dir)

    os.chdir(os.path.join(hadoop_dir, "src"))

    print("Building libhdfs")

    # Make maven-enforcer-plugin happy.
    # TODO: autodetect Java version?
    sed_inplace("pom.xml", "<javaVersion>1.7", "<javaVersion>1.8")
    sed_inplace("pom.xml", "<targetJavaVersion>1.7", "<targetJavaVersion>1.8")

    # Disable hadoop-annotations and pull them from Maven Central. This
    # module seems to require tools.jar, but even if it is in the right
    # place, the compilation still fails with cryptic error messages.
    sed_inplace(os.path.join("hadoop-common-project", "pom.xml"),
                "<module>hadoop-annotations</module>",
                "")

    run("mvn -q install -pl :hadoop-maven-plugins -am")
    run("mvn -q compile -Pnative -pl :hadoop-hdfs -am",
        env=dict(os.environ, CFLAGS="-fPIC"))

    libhdfs_dir = os.environ["LIBHDFS_DIR"]
    maybe_makedirs(libhdfs_dir)
    print("Copying libhdfs into " + libhdfs_dir)
    os.chdir(os.path.join("hadoop-hdfs-project", "hadoop-hdfs"))

    for file in [
        "target/native/target/usr/local/lib/libhdfs.a",
        "src/main/native/libhdfs/hdfs.h"
    ]:
        shutil.copy(os.path.join(*file.split("/")), libhdfs_dir)
