from __future__ import print_function, unicode_literals

import glob
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

    # HACK: library name was changed in the latest version.
    sed_inplace("CMakeLists.txt", "dmlccore", "dmlc")

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
        # Remove once https://github.com/dmlc/xgboost/pull/2379 is merged.
        sed_inplace("xgboost4j/src/native/xgboost4j.cpp",
                    "jint JNI_OnLoad",
                    "JNIEXPORT jint JNICALL JNI_OnLoad")
        sed_inplace("xgboost4j/src/native/xgboost4j.cpp",
                    "cbatch.offset = reinterpret_cast<long *>",
                    "cbatch.offset = reinterpret_cast<jlong *>")

        with cd(".."):
            maybe_makedirs("build")
            with cd("build"):
                run("cmake .. -DJVM_BINDINGS:BOOL=ON -DUSE_OPENMP:BOOL=ON")
                run("cmake --build . --target ALL_BUILD")

        # Back to jvm-packages.
        resources_dir = os.path.join("xgboost4j", "src", "main", "resources")
        shutil.copytree(os.path.join("..", "lib"), resources_dir)

        # Copy Python to native resources.
        shutil.copy(os.path.join("..", "dmlc-core", "tracker",
                                 "dmlc_tracker", "tracker.py"),
                    resources_dir)

        # Copy test data files
        maybe_makedirs(
            os.path.join("xgboost4j-spark", "src", "test", "resources"))
        with cd(os.path.join("..", "demo", "regression")):
            run("{} mapfeat.py".format(sys.executable))
            run("{} mknfold.py machine.txt 1".format(sys.executable))

        for file in glob.glob(
                os.path.join("..", "demo", "regression", "machine.txt.t*")):
            shutil.copy(file, "xgboost4j-spark/src/test/resources")
        for file in glob.glob(
                os.path.join("..", "demo", "data", "agaricus.*")):
            shutil.copy(file, "xgboost4j-spark/src/test/resources")

        with open("create_jni.bat", "w"):
            pass  # Erase. We've done all the work.

    run("mvn -q install -pl :xgboost4j,:xgboost4j-spark "
        "-DskipTests -Dmaven.test.skip",
        env=dict(os.environ, HADOOP_HOME="."))
