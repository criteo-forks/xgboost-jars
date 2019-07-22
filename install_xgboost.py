"""
Builds the JVM bindings for the latest xgboost.

Environment variables:
* XGBOOST_VERSION
* SCALA_VERSION
* SPARK_VERSION
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

    run("mvn -q install -pl :xgboost4j,:xgboost4j-spark "
        "-DskipTests -Dmaven.test.skip",
        env=dict(os.environ,
                 HADOOP_HOME=xgboost_dir,
                 HADOOP_HDFS_HOME=xgboost_dir))
