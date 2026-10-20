FROM ubuntu@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac
ENV TZ=Etc/UTC DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends sudo python3 python-is-python3 tar xz-utils wget curl git ca-certificates && dpkg-query -W > /toolchain-bootstrap-packages.txt
WORKDIR /work/build_tools
CMD ["bash", "/work/organisationos/container/build.sh"]
