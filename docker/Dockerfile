# vi:syntax=dockerfile
FROM ubuntu:xenial
MAINTAINER Daniele Viganò <daniele@openquake.org>

RUN echo "deb     http://qgis.org/debian-ltr xenial main" >> /etc/apt/sources.list && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-key CAEB3DC3BDF7FB45 && \
    apt update && \
    apt upgrade -y && \
    apt -q install -y build-essential git sudo software-properties-common xvfb zip \
                   python-qt4-dev pyqt4-dev-tools \
                   python-pip python-mock python-nose \
                   python-nose-exclude python-scipy \
                   texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended && \
    pip install sphinx==1.4.9 sphinx_rtd_theme

RUN add-apt-repository -y ppa:openquake/saga && \
    apt update && \
    apt install -y qgis python-qgis \
                   saga python-saga && \
    apt clean all

ARG uid=1000
RUN useradd -m -u $uid builder && \
    echo 'builder ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER builder
ADD gitconfig /home/builder/.gitconfig

WORKDIR /io

ENV DISPLAY=:99
ENV PYTHONPATH=/io

ENTRYPOINT ["/bin/bash", "/io/docker/run_make.sh"]
