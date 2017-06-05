from __future__ import print_function, unicode_literals

import glob
import os
import re
import shutil
import sys
from _internal import run, sed_inplace, maybe_makedirs, cd


def library_names():
    if sys.platform == "linux2":
        name = "libxgboost4j.so"
        return name, name
    elif sys.platform == "darwin":
        name = "libxgboost4j.dylib"
        return name, name
    else:
        return "libxgboost4j.dll", "xgboost4j.dll"


if __name__ == "__main__":
    os.chdir("xgboost")
    maybe_makedirs(os.path.join("lib", "native"))
    maybe_makedirs(os.path.join("lib", "include"))
    libhdfs_shared = \
        "hdfs.dll" if sys.platform in ["cygwin", "win32"] else "libhdfs.so"
    libhdfs_static = \
        "hdfs.lib" if sys.platform in ["cygwin", "win32"] else "libhdfs.a"

    shutil.copy(os.path.join(os.environ["LIBHDFS_DIR"], libhdfs_static),
                os.path.join("lib", "native"))
    shutil.copy(os.path.join(os.environ["LIBHDFS_DIR"], libhdfs_shared),
                os.path.join("lib", "native"))
    shutil.copy(os.path.join(os.environ["LIBHDFS_DIR"], "hdfs.h"),
                os.path.join("lib", "include"))

    # HACK: library name was changed in the latest version.
    sed_inplace("CMakeLists.txt", "dmlccore", "dmlc")

    sed_inplace("CMakeLists.txt", '"USE_HDFS": "OFF"', '"USE_HDFS": "ON"')

    # HACK: patch FindHDFS to support Windows.
    sed_inplace(
        "dmlc-core/cmake/Modules/FindHDFS.cmake",
        "libhdfs.a",
        "${CMAKE_STATIC_LIBRARY_PREFIX}hdfs${CMAKE_STATIC_LIBRARY_SUFFIX}")

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

    run("mvn -q install -pl :xgboost4j,:xgboost4j-spark "
        "-DskipTests -Dmaven.test.skip",
        env=dict(os.environ, HADOOP_HOME="."))
