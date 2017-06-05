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
        "linux2": "libhdfs.so",
        "darwin": "libhdfs.dylib"
    }[sys.platform]
    libhdfs_static = {
        "win32": "hdfs.lib",
        "linux2": "libhdfs.a",
        "darwin": "libhdfs.a"
    }[sys.platform]

    shutil.copy(os.path.join(os.environ["LIBHDFS_DIR"], libhdfs_static),
                os.path.join("lib", "native"))
    shutil.copy(os.path.join(os.environ["LIBHDFS_DIR"], libhdfs_shared),
                os.path.join("lib", "native"))
    shutil.copy(os.path.join(os.environ["LIBHDFS_DIR"], "hdfs.h"), "include")

    # HACK: library name was changed in the latest version.
    sed_inplace("CMakeLists.txt", "dmlccore", "dmlc")

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

    sed_inplace("create_jni.py", '"USE_HDFS": "OFF"', '"USE_HDFS": "ON"')

    run("mvn -q install -pl :xgboost4j,:xgboost4j-spark "
        "-DskipTests -Dmaven.test.skip",
        env=dict(os.environ, HADOOP_HOME=xgboost_dir))
