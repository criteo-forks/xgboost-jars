from __future__ import print_function, unicode_literals

import os
import re
import shutil
import sys
from _internal import run, sed_inplace, maybe_makedirs, cd


if __name__ == "__main__":
    os.chdir("xgboost")
    maybe_makedirs(os.path.join("lib", "native"))
    libhdfs_static = \
        "hdfs.lib" if sys.platform in ["cygwin", "win32"] else "libhdfs.a"

    shutil.copy(os.path.join(os.environ["LIBHDFS_DIR"], libhdfs_static),
                os.path.join("lib", "native"))
    shutil.copy(os.path.join(os.environ["LIBHDFS_DIR"], "hdfs.h"),
                os.path.join("dmlc-core", "include"))

    shutil.copy(os.path.join("..", "config_" + sys.platform + ".mk"),
                "config.mk")

    os.chdir("jvm-packages")
    run("mvn -q -B versions:set -DnewVersion=" + os.environ["XGBOOST_VERSION"])

    # versions:update-property only updates properties which define
    # artifact versions, therefore we have to resort to sed.
    scala_version = os.environ["SCALA_VERSION"]
    [scala_binary_version] = re.findall(r"^(2\.1[012])\.\d+", scala_version)
    sed_inplace("pom.xml",
                "<scala.binary.version>2.11",
                "<scala.binary.version>" + scala_binary_version)
    run("mvn -q versions:update-property -Dproperty=scala.version "
        "-DnewVersion=[{}]".format(scala_version))
    run("mvn -q versions:update-property -Dproperty=spark.version "
        "-DnewVersion=[{}]".format(os.environ["SPARK_VERSION"]))

    if sys.platform in ["cygwin", "win32"]:
        with cd(".."):
            run("mingw32-make jvm")

    run("mvn -q install -pl :xgboost4j,:xgboost4j-spark "
        "-DskipTests -Dmaven.test.skip",
        env=dict(os.environ, HADOOP_HOME="."))
