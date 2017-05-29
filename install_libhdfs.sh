#!/usr/bin/env bash

set -e -x

if [[ "$TRAVIS_OS_NAME" == "osx" ]]; then
    brew update >/dev/null
    brew install protobuf@2.5
    export HADOOP_PROTOC_CDH5_PATH="/usr/local/opt/protobuf@2.5/bin/protoc"

    sudo mkdir `/usr/libexec/java_home`/Classes
    sudo ln -s `/usr/libexec/java_home`/lib/tools.jar \
         `/usr/libexec/java_home`/Classes/classes.jar
fi

pushd $PWD

echo "Building libhdfs"
wget -qc http://archive.cloudera.com/cdh5/cdh/5/hadoop-${HADOOP_VERSION}.tar.gz
tar -zxf hadoop-${HADOOP_VERSION}.tar.gz
cd hadoop-$HADOOP_VERSION/src

# Make maven-enforcer-plugin happy.
sed -i -e 's|<javaVersion>1.7|<javaVersion>1.8|' pom.xml
sed -i -e 's|<targetJavaVersion>1.7|<targetJavaVersion>1.8|' pom.xml

# Disable hadoop-annotations which requires tools.jar
sed -i -e 's|<module>hadoop-annotations</module>||' hadoop-common-project/pom.xml

mvn -q install -pl :hadoop-maven-plugins -am
CFLAGS=-fPIC mvn -q compile -Pnative -pl :hadoop-hdfs -am

echo "Copying libhdfs into $LIBHDFS_DEV"
mkdir -p $LIBHDFS_DEV
cd hadoop-hdfs-project/hadoop-hdfs
cp target/native/target/usr/local/lib/libhdfs.a \
   src/main/native/libhdfs/hdfs.h \
   $LIBHDFS_DEV

popd
