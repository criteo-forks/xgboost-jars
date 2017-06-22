set -xe

mkdir -p $LIBHDFS_DIR
if [ ! -z `find $LIBHDFS_DIR -prune -empty` ]; then python ./install_libhdfs.py; fi
python ./install_xgboost.py
