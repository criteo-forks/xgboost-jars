xgboost4j
=========

[![Build Status](https://travis-ci.org/criteo-forks/xgboost-jars.svg?branch=master)](https://travis-ci.org/criteo-forks/xgboost-jars)
[![Build status](https://ci.appveyor.com/api/projects/status/puy22q7qp1u8eg7f/branch/master?svg=true)](https://ci.appveyor.com/project/superbobry/xgboost-jars/branch/master)

Repository to build [xgboost4j](https://github.com/criteo-forks/xgboost) JARs.

Build
-----

The build would always use the *latest* version of xgboost and its submodules.
Sadly, there is no way around it at the moment, as the submodules are pinned
to specific commits, and `dmlc-core` received quite a few patches to be buildable
on both CIs. In the future, this behaviour could be safely removed.

Otherwise, the following versions of the dependencies are used

```
HADOOP_VERSION=2.6.0-cdh5.5.0
SPARK_VERSION=2.4.1
SCALA_VERSION=2.11.12
```

You could probably change them to more recent/different version, but this has
not been validated yet.

#### Windows

The Windows build is x64 only and uses Visual Studio 2015.

#### Linux

The Linux build is done inside a CentOS6 Docker container to make sure the
resulting JARs can be executed on ancient Linux distributions like CentOS.

Release
-------

To make a release:

- Bump `XGBOOST_BASE_VERSION` in `.travis.yml` and `appveyor.yml`.
- Tag `master` with `XGBOOST_BASE_VERSION`.
- Wait :)
