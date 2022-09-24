FROM rockylinux:9

ENV TOR_VERSION 0.4.7.10
LABEL name="Tor service client"
LABEL license="GNU"
LABEL url="https://www.torproject.org"
LABEL github-url="https://github.com/idkme24"

## Install Dependencies and Updates
RUN dnf install libevent compat-openssl11 python3-pyyaml python3 -y
RUN dnf update -y && dnf clean all

## Create User and Group
RUN groupadd --gid 1001 torservice
RUN useradd --uid 1000 --gid 1001 -d /tor torservice

## Define Storage
ENV DATA_DIR=/tor
VOLUME [ "${DATA_DIR}" ]
WORKDIR ${DATA_DIR}

## Install Tor Binary and Entrypoint Scripts
COPY tor /usr/local/bin/
COPY torrc /etc/
COPY entrypoint.py /usr/local/bin/
COPY init.sh /usr/local/bin/init.sh
RUN chmod 755 /usr/local/bin/entrypoint.py && chmod 755 /usr/local/bin/tor && chmod 755 /usr/local/bin/init.sh

## Open Default SOCKS Port
EXPOSE 9050/tcp

ENTRYPOINT ["/usr/local/bin/init.sh"]
