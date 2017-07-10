"""
Builds the JVM bindings for the latest xgboost.

Environment variables:
* XGBOOST_VERSION
* SCALA_VERSION
* SPARK_VERSION
* LIBHDFS_DIR containing libhdfs.{so,a} and hdfs.h
"""

from __future__ import print_function, unicode_literals

import os
import re
import shutil
import sys
from _internal import run, sed_inplace, maybe_makedirs


if __name__ == "__main__":
    os.chdir("xgboost")
    xgboost_dir = os.getcwd()
    maybe_makedirs(os.path.join("lib", "native"))
    maybe_makedirs(os.path.join("lib", "include"))

    libhdfs_shared = {
        "win32": "hdfs.dll",
        "linux": "libhdfs.so",
        "darwin": "libhdfs.dylib"
    }[sys.platform]
    libhdfs_static = {
        "win32": "hdfs.lib",
        "linux": "libhdfs.a",
        "darwin": "libhdfs.a"
    }[sys.platform]

    libhdfs_dir = os.environ["LIBHDFS_DIR"]
    shutil.copy(os.path.join(libhdfs_dir, libhdfs_static),
                os.path.join("lib", "native"))
    shutil.copy(os.path.join(libhdfs_dir, libhdfs_shared),
                os.path.join("lib", "native"))
    shutil.copy(os.path.join(libhdfs_dir, "hdfs.h"), "include")

    if sys.platform == "win32":
        maybe_makedirs("bin")
        shutil.copy(os.path.join(libhdfs_dir, "winutils.exe"), "bin")

    # HACK: library name was changed in the latest version.
    sed_inplace("CMakeLists.txt", "dmlccore", "dmlc")

    # HACK: patch FindHDFS to support Windows.
    sed_inplace(
        "dmlc-core/cmake/Modules/FindHDFS.cmake",
        "libhdfs.a",
        "${CMAKE_STATIC_LIBRARY_PREFIX}hdfs${CMAKE_STATIC_LIBRARY_SUFFIX}")

    # HACK: link with static libhdfs.
    sed_inplace(
        "dmlc-core/CMakeLists.txt",
        "list(APPEND dmlccore_LINKER_LIBS ${HDFS_LIBRARIES}",
        "list(APPEND dmlccore_LINKER_LIBS ${HDFS_STATIC_LIB}")

    # HACK: add missing header.
    sed_inplace(
        "dmlc-core/src/io/hdfs_filesys.cc",
        "// Copyright by Contributors",
        "#include <algorithm>")

    os.chdir("jvm-packages")
    run("mvn -q -B versions:set -DnewVersion=" + os.environ["XGBOOST_VERSION"])

    # versions:update-property only updates properties which define
    # artifact versions, therefore we have to resort to sed.
    scala_version = os.environ["SCALA_VERSION"]
    [scala_binary_version] = re.findall(r"^(2\.1[012])\.\d+", scala_version)
    sed_inplace("pom.xml",
                "<scala.binary.version>[^<]+",
                "<scala.binary.version>" + scala_binary_version, regex=True)
    sed_inplace("pom.xml",
                "<scala.version>[^<]+",
                "<scala.version>" + scala_version, regex=True)
    sed_inplace("pom.xml",
                "<spark.version>[^<]+",
                "<spark.version>" + os.environ["SPARK_VERSION"], regex=True)

    # HACK: build release.
    sed_inplace("create_jni.py",
                "cmake ..",
                "cmake .. -DCMAKE_BUILD_TYPE=Release ")

    sed_inplace("create_jni.py", '"USE_HDFS": "OFF"', '"USE_HDFS": "ON"')

    run("mvn -q install -pl :xgboost4j,:xgboost4j-spark "
        "-DskipTests -Dmaven.test.skip",
        env=dict(os.environ, HADOOP_HDFS_HOME=xgboost_dir))
