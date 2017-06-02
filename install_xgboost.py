from __future__ import print_function, unicode_literals

import os
import re
import shutil
import sys
from _internal import run, sed_inplace, maybe_makedirs


if __name__ == "__main__":
    os.chdir("xgboost")
    maybe_makedirs(os.path.join("lib", "native"))
    libhdfs_static = \
        "hdfs.lib" if sys.platform in ["cygwin", "win32"] else "libhdfs.a"

    shutil.copy(os.path.join(os.environ["LIBHDFS_DIR"], libhdfs_static),
                os.path.join("lib", "native"))
    shutil.copy(os.path.join(os.environ["LIBHDFS_DIR"], "hdfs.h"),
                os.path.join("dmlc-core", "include"))

    if sys.platform == "darwin":
        # See https://github.com/dmlc/dmlc-core/pull/258.
        sed_inplace(os.path.join("dmlc-core", "make", "dmlc.mk"),
                    "-rpath=$(LIBJVM)",
                    "-rpath,$(LIBJVM)")

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

    run("mvn -q install -pl :xgboost4j,:xgboost4j-spark "
        "-DskipTests -Dmaven.test.skip",
        env=dict(os.environ, HADOOP_HOME="."))
