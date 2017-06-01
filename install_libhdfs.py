from __future__ import print_function, unicode_literals

import os
import shutil
import subprocess
import tarfile
import zipfile
try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, "wb")

from _internal import run, sed_inplace, maybe_makedirs


def install_dependencies():
    if "TRAVIS" in os.environ:
        if os.environ["TRAVIS_OS_NAME"] == "osx":
            run("brew install protobuf@2.5", stdout=open(os.devnull, "wb"))
            os.environ["HADOOP_PROTOC_CDH5_PATH"] = \
                "/usr/local/opt/protobuf@2.5/bin/protoc"

            # Make maven-antrun-plugin happy and put tools.jar to the
            # magical place.
            java_home = os.environ["JAVA_HOME"] = subprocess.check_output(
                "/usr/libexec/java_home").strip().decode()
            # Not pure Python because we need sudo.
            run("sudo mkdir " + os.path.join(java_home, "Classes"))
            run("sudo ln -s {} {}".format(
                os.path.join(java_home, "lib", "tools.jar"),
                os.path.join(java_home, "Classes", "classes.jar")))
    elif "APPVEYOR" in os.environ:
        protobuf_archive, _headers = urlretrieve(
            "https://github.com/google/protobuf/releases/download/"
            "v2.5.0/protoc-2.5.0-win32.zip")
        with zipfile.ZipFile(protobuf_archive, "r") as zf:
            zf.extractall()

        os.environ["HADOOP_PROTOC_CDH5_PATH"] = \
            os.path.join(os.getcwd(), "protoc.exe")


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
