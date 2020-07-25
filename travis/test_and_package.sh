set -xe

export HADOOP_HOME=$PWD/xgboost
export HADOOP_HDFS_HOME=$PWD/xgboost

cd xgboost/jvm-packages
mvn -q package -pl xgboost4j,xgboost4j-spark -DskipTests -Dmaven.test.skip

cp xgboost4j/target/xgboost4j_$SCALA_BINARY_VERSION-$XGBOOST_VERSION.jar \
   $TRAVIS_BUILD_DIR/xgboost4j_$SCALA_BINARY_VERSION-$XGBOOST_VERSION-$TRAVIS_OS_NAME.jar
cp xgboost4j-spark/target/xgboost4j-spark_$SCALA_BINARY_VERSION-$XGBOOST_VERSION.jar \
   $TRAVIS_BUILD_DIR/xgboost4j-spark_$SCALA_BINARY_VERSION-$XGBOOST_VERSION.jar
