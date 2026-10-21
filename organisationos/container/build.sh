#!/bin/bash
set -euo pipefail
# build_tools/version differs from the pinned DocumentServer release. Never inherit its default.
export PRODUCT_VERSION=10.0.0
export BUILD_NUMBER=2
mkdir -p /work/build-evidence
exec > >(tee /work/build-evidence/build.log) 2>&1
trap 'status=$?; printf "%s\n" "$status" > /work/build-evidence/exit-status; dpkg-query -W > /work/build-evidence/toolchain-packages.tsv; exit "$status"' EXIT
cd /work/build_tools/tools/linux
if [ ! -d python3 ]; then bash python.sh; fi
rm -f packages_complete
./python3/bin/python3 deps.py
bash cmake.sh
if [ ! -d qt_build/Qt-5.9.9 ]; then ./python3/bin/python3 qt_binary_fetch.py amd64; fi
if [ ! -d sysroot/ubuntu16-amd64-sysroot ]; then cd sysroot; ../python3/bin/python3 fetch.py amd64; cd ..; fi
# Apply reviewed server overlays exactly once; never let patch guess the reverse direction.
for overlay in server-redact-jwt-logs.patch server-snapshot-identity.patch; do
  if ! patch --force --reverse --dry-run -p1 -d /work/server < /work/organisationos/patches/$overlay >/dev/null 2>&1; then
    patch --batch --forward -p1 -d /work/server < /work/organisationos/patches/$overlay
  fi
done
grep -Fq 'JWT verification rejected: %s' /work/server/DocService/sources/DocsCoServer.js
if grep -Fq 'checkJwt error: name = %s message = %s token = %s' /work/server/DocService/sources/DocsCoServer.js; then exit 1; fi
grep -Fq 'organisationosSnapshot' /work/server/FileConverter/sources/converter.js
grep -Fq 'organisationos-converted-changes-v2' /work/server/Common/sources/oosSnapshotIdentity.js
cd /work/build_tools
./tools/linux/python3/bin/python3 configure.py --module server --update 0 --sysroot 1 --platform linux_64 --qt-dir /work/build_tools/tools/linux/qt_build/Qt-5.9.9
./tools/linux/python3/bin/python3 make.py

# A successful build must still use the reviewed privacy-patched source.
grep -Fq 'JWT verification rejected: %s' /work/server/DocService/sources/DocsCoServer.js
grep -Fq 'organisationosSnapshot' /work/server/DocService/sources/canvasservice.js
