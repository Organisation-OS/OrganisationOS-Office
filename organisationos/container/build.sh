#!/bin/bash
set -euo pipefail
mkdir -p /work/build-evidence
exec > >(tee /work/build-evidence/build.log) 2>&1
trap 'status=$?; printf "%s\n" "$status" > /work/build-evidence/exit-status; dpkg-query -W > /work/build-evidence/toolchain-packages.tsv; exit "$status"' EXIT
cd /work/build_tools/tools/linux
if [ ! -d python3 ]; then bash python.sh; fi
if [ ! -f packages_complete ]; then ./python3/bin/python3 deps.py; bash cmake.sh; fi
if [ ! -d qt_build/Qt-5.9.9 ]; then ./python3/bin/python3 qt_binary_fetch.py amd64; fi
if [ ! -d sysroot/ubuntu16-amd64-sysroot ]; then cd sysroot; ../python3/bin/python3 fetch.py amd64; cd ..; fi
cd /work/build_tools
./tools/linux/python3/bin/python3 configure.py --module server --update 0 --sysroot 1 --platform linux_64 --qt-dir /work/build_tools/tools/linux/qt_build/Qt-5.9.9
./tools/linux/python3/bin/python3 make.py
