et -e
set -x

if [ $# -ne 1 ]; then
  echo "Usage: $0 [spark version]"
  exit 1
fi

spark_version=$1

BASEDIR="$( cd "$( dirname "$0" )" && pwd )" # the directory of this file
IMG_NAME="xgboost4j-build"

docker build -t ${IMG_NAME} "${BASEDIR}" # build and tag the Dockerfile

docker run --rm \
  --memory 8g \
  --env JAVA_OPTS="-Xmx6g" \
  --env MAVEN_OPTS="-Xmx2g" \
  --volume "${BASEDIR}/../xgboost":/xgboost \
  --volume "${BASEDIR}/../.m2":/root/.m2 \
  ${IMG_NAME} ../build.sh ${spark_version}
