set -xe

# Clean the yum cache
yum -y clean all
yum -y clean expire-cache

# Install all the needed packages.
yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm

yum -y install wget tar cmake3 zlib-devel \
    python34 java-1.8.0-openjdk-devel maven

# Setup SCL for newer GCC.
yum -y install centos-release-scl-rh
yum -y install devtoolset-4-{gcc,gcc-c++}

source /opt/rh/devtoolset-4/enable
export CC=/opt/rh/devtoolset-4/root/usr/bin/gcc
export CXX=/opt/rh/devtoolset-4/root/usr/bin/c++

cd /xgboost-jars

# No Maven on CentOS6.
wget -qc http://mirrors.ircam.fr/pub/apache/maven/maven-3/3.5.0/binaries/apache-maven-3.5.0-bin.tar.gz
tar -zxf apache-maven-3.5.0-bin.tar.gz
export PATH=$PWD/apache-maven-3.5.0/bin:$PATH

# CMake3 is not aliased to ``cmake``
ln -s /usr/bin/cmake3 /usr/bin/cmake
rm /usr/bin/python
ln -s /usr/bin/python3 /usr/bin/python

export JAVA_HOME=/usr/lib/jvm/java

# For some reason CMake wouldn't pick up the compilers from devtoolset.
# Point it to them manually.
mkdir -p xgboost/build
pushd xgboost/build
cmake .. -DCMAKE_C_COMPILER=$CC -DCMAKE_CXX_COMPILER=$CXX
popd

sh travis/install.sh
TRAVIS_BUILD_DIR=$PWD sh travis/test_and_package.sh
