"""
Downloads the latest release from GitHub and merges platform-specific
JARs into a single ``xgboost4j-VERSION.jar``.
"""

from __future__ import print_function

import json
import glob
import os
import sys
from collections import defaultdict
from zipfile import ZipFile

try:
    from urllib import urlretrieve
    from urllib2 import urlopen
except ImportError:  # 3.X
    from urllib.request import urlretrieve, urlopen


def merge_zip_files(target, sources):
    seen = set()
    with ZipFile(target, "w") as zf_dst:
        for path in sources:
            with ZipFile(path, "r") as zf_src:
                for name in zf_src.namelist():
                    if name in seen:
                        continue

                    seen.add(name)
                    zf_dst.writestr(name, zf_src.open(name).read())


if __name__ == "__main__":
    response = urlopen(
        "https://api.github.com/repos/criteo-forks/xgboost-jars/releases")
    releases = json.load(response)

    latest_release = max(releases, key=lambda r: r["tag_name"])
    with open("VERSION", "w") as f:
        f.write(latest_release["tag_name"])

    print("Fetching", latest_release["tag_name"])

    for asset in latest_release["assets"]:
        asset_url = asset["browser_download_url"]
        urlretrieve(asset_url, os.path.basename(asset_url))

    for scala_binary_tag in ["2.10", "2.11"]:
        def versioned(s):
            return s.format(latest_release["tag_name"] + "_" + scala_binary_tag)

        native_jars = [
            versioned("xgboost4j-{}-win64.jar"),
            versioned("xgboost4j-{}-osx.jar"),
            versioned("xgboost4j-{}-linux.jar")
        ]
        merge_zip_files(versioned("xgboost4j-{}.jar"), native_jars)
        for jar in native_jars:
            os.remove(jar)

    print(*glob.glob("xgboost*"), sep="\n")
