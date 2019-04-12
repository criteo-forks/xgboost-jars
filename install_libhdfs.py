"""
Downloads and builds libhdfs for a given CDH Hadoop version.

Environment variables:
* HADOOP_VERSION
* LIBHDFS_DIR

Assumptions:
* Java 8 is installed and available in $PATH.
* (OS X) The user has passwordless sudo.
* (Windows) Visual Studio 14 is available.
"""

from __future__ import print_function, unicode_literals

import os
import re
import shutil
import subprocess
import sys
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

from _internal import run, sed_inplace, maybe_makedirs, cd


RUNTIME_LIB_OVERRIDE = """\
if(MSVC)
    set(variables
        CMAKE_C_FLAGS_DEBUG
        CMAKE_C_FLAGS_MINSIZEREL
        CMAKE_C_FLAGS_RELEASE
        CMAKE_C_FLAGS_RELWITHDEBINFO
        CMAKE_CXX_FLAGS_DEBUG
        CMAKE_CXX_FLAGS_MINSIZEREL
        CMAKE_CXX_FLAGS_RELEASE
        CMAKE_CXX_FLAGS_RELWITHDEBINFO
    )
    foreach(variable ${variables})
        if(${variable} MATCHES "/MD")
            string(REGEX REPLACE "/MD" "/MT" ${variable} "${${variable}}")
        endif()
    endforeach()
endif()
"""


def detect_java_version():
    output = subprocess.check_output(
        "java -version", stderr=subprocess.STDOUT, shell=True).decode()
    [java_version] = re.findall(r"build (1.\d).0", output)
    return java_version


def install_dependencies():
    if sys.platform == "linux":
        protobuf_archive, _headers = urlretrieve(
            "https://github.com/google/protobuf/releases/download/"
            "v2.5.0/protobuf-2.5.0.zip")
        with zipfile.ZipFile(protobuf_archive, "r") as zf:
            zf.extractall()

        with cd("protobuf-2.5.0"):
            run("sh configure")
            run("make")

            os.environ["HADOOP_PROTOC_CDH5_PATH"] = \
                os.path.join(os.getcwd(), "src", "protoc")
    elif sys.platform == "darwin":
        protobuf_archive, _headers = urlretrieve(
            "https://github.com/google/protobuf/releases/download/"
            "v2.5.0/protobuf-2.5.0.zip")
        with zipfile.ZipFile(protobuf_archive, "r") as zf:
            zf.extractall()

        with cd("protobuf-2.5.0"):
            run("sh configure")
            run("make")

            os.environ["HADOOP_PROTOC_CDH5_PATH"] = \
                os.path.join(os.getcwd(), "src", "protoc")
        # Make maven-antrun-plugin happy and put tools.jar to the
        # magical place.
        java_home = os.environ["JAVA_HOME"] = subprocess.check_output(
            "/usr/libexec/java_home").strip().decode()
        # Not pure Python because we need sudo.
        run("sudo mkdir -p " + os.path.join(java_home, "Classes"))
        run("sudo ln -nsf {} {}".format(
            os.path.join(java_home, "lib", "tools.jar"),
            os.path.join(java_home, "Classes", "classes.jar")))
    elif sys.platform in ["cygwin", "win32"]:
        protobuf_archive, _headers = urlretrieve(
            "https://github.com/google/protobuf/releases/download/"
            "v2.5.0/protoc-2.5.0-win32.zip")
        with zipfile.ZipFile(protobuf_archive, "r") as zf:
            zf.extractall()

        os.environ["HADOOP_PROTOC_CDH5_PATH"] = \
            os.path.join(os.getcwd(), "protoc.exe")


def build():
    # Make maven-enforcer-plugin happy.
    java_version = detect_java_version()
    sed_inplace("pom.xml", "<javaVersion>1.7", "<javaVersion>" + java_version)
    sed_inplace("pom.xml", "<targetJavaVersion>1.7",
                "<targetJavaVersion>" + java_version)

    # Disable hadoop-annotations and pull them from Maven Central. This
    # module seems to require tools.jar, but even if it is in the right
    # place, the compilation still fails with cryptic error messages.
    sed_inplace(os.path.join("hadoop-common-project", "pom.xml"),
                "<module>hadoop-annotations</module>",
                "")

    if sys.platform in ["cygwin", "win32"]:
        target = "native-win"

        for sln in [
            "hadoop-common-project\\hadoop-common\\src\\main\\native\\native.sln",
            "hadoop-common-project\\hadoop-common\\src\\main\\winutils\\winutils.sln"
        ]:
            run("devenv /upgrade " + sln)

        sed_inplace(
            "hadoop-hdfs-project\\hadoop-hdfs\\pom.xml",
            "Visual Studio 10",
            "Visual Studio 14")

        hdfs_cmake_path = "hadoop-hdfs-project\\hadoop-hdfs\\src\\CMakeLists.txt"
        with open(hdfs_cmake_path, "a") as cml:
            cml.write(RUNTIME_LIB_OVERRIDE)
    else:
        target = "native"

    run("mvn -q install -pl :hadoop-maven-plugins -am")
    run("mvn -q compile -P{} -pl :hadoop-hdfs -am".format(target),
        env=dict(os.environ, CFLAGS="-fPIC"))


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

    print("Building libhdfs")
    with cd(os.path.join(hadoop_dir, "src")):
        build()

        libhdfs_dir = os.environ["LIBHDFS_DIR"]
        maybe_makedirs(libhdfs_dir)
        print("Copying libhdfs into " + libhdfs_dir)

        if sys.platform in ["cygwin", "win32"]:
            libhdfs_files = [
                "target\\native\\target\\bin\\RelWithDebInfo\\hdfs.dll",
                "target\\native\\target\\bin\\RelWithDebInfo\\hdfs.lib",
                "src\\main\\native\\libhdfs\\hdfs.h"
            ]
        elif sys.platform == "linux":
            libhdfs_files = [
                "target/native/target/usr/local/lib/libhdfs.a",
                "target/native/target/usr/local/lib/libhdfs.so",
                "src/main/native/libhdfs/hdfs.h"
            ]
        else:
            libhdfs_files = [
                "target/native/target/usr/local/lib/libhdfs.a",
                "target/native/target/usr/local/lib/libhdfs.dylib",
                "src/main/native/libhdfs/hdfs.h"
            ]

        with cd(os.path.join("hadoop-hdfs-project", "hadoop-hdfs")):
            for file in libhdfs_files:
                shutil.copy(file, libhdfs_dir)

        if sys.platform == "win32":
            with cd(os.path.join("hadoop-common-project", "hadoop-common")):
                shutil.copy(os.path.join("target", "bin", "winutils.exe"),
                            libhdfs_dir)
