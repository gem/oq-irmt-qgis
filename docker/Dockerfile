# vi:syntax=dockerfile
FROM ubuntu:bionic
MAINTAINER GEM Foundation <devops@openquake.org>

ENV DEBIAN_FRONTEND noninteractive

RUN apt update && apt -q install -y gnupg2 

RUN echo "deb https://qgis.org/debian bionic main " >> /etc/apt/sources.list && \
   apt-key adv --keyserver keyserver.ubuntu.com --recv-key F7E06F06199EF2F2 && \
   apt update &&  apt dist-upgrade -y 
RUN apt -q install -y locales build-essential git sudo xvfb zip \
                   qt5-default pyqt5-dev pyqt5-dev-tools \
                   python3-pyqt5.qtwebkit python3-pip \
                   python3-mock python3-nose \
                   python3-nose-exclude \
                   ghostscript \
                   texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended && \
    pip3 install sphinx==1.4.9 sphinx_rtd_theme && \
    locale-gen en_US.UTF-8

# Perform cache invalidation when new packages are out
# a new 'apt update' is always performed to comply
# with the cache invalidation
ADD http://qgis.org/debian/dists/bionic/main/binary-amd64/Packages /tmp/nocache.json
RUN apt update && \
    apt install -y qgis python-qgis && \
    apt clean all
#  instead of use ARG use: --build-arg uid=$(id -u)
#ARG uid=988
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
