set -xe

sh travis/install.sh
TRAVIS_BUILD_DIR=$PWD sh travis/test_and_package.sh
