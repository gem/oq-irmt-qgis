# vi:syntax=dockerfile
FROM ubuntu:xenial
MAINTAINER Daniele Viganò <daniele@openquake.org>

ENV DEBIAN_FRONTEND noninteractive

RUN apt update && apt -q install -y gnupg2 && \
    echo "deb     http://qgis.org/debian-ltr xenial main" >> /etc/apt/sources.list && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-key CAEB3DC3BDF7FB45 && \
    apt update && \
    apt upgrade -y && \
    apt -q install -y locales build-essential git sudo software-properties-common xvfb zip \
                   python-qt4-dev pyqt4-dev-tools \
                   python-pip python-mock python-nose \
                   python-nose-exclude python-scipy \
                   texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended && \
    pip install sphinx==1.4.9 sphinx_rtd_theme && \
    locale-gen en_US.UTF-8

# Perform cache invalidation when new packages are out
# a new 'apt update' is always performed to comply
# with the cache invalidation
ADD http://qgis.org/debian-ltr/dists/xenial/main/binary-amd64/Packages /tmp/nocache.json
RUN apt install -y qgis python-qgis && \
    apt clean all

ARG uid=1000
RUN useradd -m -u $uid builder && \
    echo 'builder ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER builder
ADD gitconfig /home/builder/.gitconfig

WORKDIR /io

ENV LANG en_US.UTF-8
ENV DISPLAY=:99
ENV PYTHONPATH=/io
ENV PYTHONIOENCODING=utf_8

ENTRYPOINT ["/bin/bash", "/io/docker/run_make.sh"]
