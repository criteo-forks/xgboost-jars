set -xe

export HADOOP_HOME=$PWD/xgboost
export HADOOP_HDFS_HOME=$PWD/xgboost

cd xgboost/jvm-packages
mvn -q package -pl :xgboost4j,:xgboost4j-spark -Prelease

mv xgboost4j/target/xgboost4j-$XGBOOST_VERSION.jar \
   $TRAVIS_BUILD_DIR/xgboost4j-$XGBOOST_VERSION-$TRAVIS_OS_NAME.jar
mv xgboost4j-spark/target/xgboost4j-spark-$XGBOOST_VERSION.jar \
   $TRAVIS_BUILD_DIR/xgboost4j-spark-$XGBOOST_VERSION.jar
