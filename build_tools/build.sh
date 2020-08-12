#!/bin/bash

set -e
set -x

if [ $# -ne 1 ]; then
  echo "Usage: $0 [spark version]"
  exit 1
fi

spark_version=$1

rm -rf build/
cd jvm-packages
export RABIT_MOCK=ON
mvn package -pl xgboost4j,xgboost4j-spark -Dspark.version=${spark_version} -DskipTests

set +x
set +e
