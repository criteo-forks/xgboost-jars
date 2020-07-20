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
    sed_inplace("pom.xml",
                "<artifactId>xgboost-jvm_[^<]+",
                "<artifactId>xgboost-jvm_" + scala_binary_version, regex=True)
    # HACK: build release.
    sed_inplace("create_jni.py",
                "cmake ..",
                "cmake .. -DCMAKE_BUILD_TYPE=Release ")

    os.chdir("xgboost4j")
    sed_inplace("pom.xml",
                "<artifactId>xgboost-jvm_[^<]+",
                "<artifactId>xgboost-jvm_" + scala_binary_version, regex=True)
    sed_inplace("pom.xml",
                "<artifactId>xgboost4j_[^<]+",
                "<artifactId>xgboost4j_" + scala_binary_version, regex=True)

    os.chdir("../xgboost4j-spark")
    sed_inplace("pom.xml",
                "<artifactId>xgboost-jvm_[^<]+",
                "<artifactId>xgboost-jvm_" + scala_binary_version, regex=True)
    sed_inplace("pom.xml",
                "<artifactId>xgboost4j-spark_[^<]+",
                "<artifactId>xgboost4j-spark_" + scala_binary_version, regex=True)
    sed_inplace("pom.xml",
            "<version>1.1.0</version>",
            "<version>" + os.environ["XGBOOST_VERSION"] + "</version>", regex=True)

    os.chdir("../dev")
    sed_inplace("package-linux.sh",
                "mvn --batch-mode clean package -DskipTests",
                "mvn install -pl xgboost4j,xgboost4j-spark -am -DskipTests -Dmaven.test.skip")
