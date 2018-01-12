# vi:syntax=dockerfile
FROM ubuntu:xenial
MAINTAINER Daniele Viganò <daniele@openquake.org>

RUN echo "deb     http://qgis.org/debian xenial main" >> /etc/apt/sources.list && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-key CAEB3DC3BDF7FB45 && \
    apt update && \
    apt upgrade -y && \
    apt install -y build-essential git xvfb zip \
                   python-qt4-dev pyqt4-dev-tools \
                   python-pip python-mock python-nose \
                   python-nose-exclude python-scipy \
                   texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended && \
    pip install sphinx==1.4.9 sphinx_rtd_theme

RUN apt install -y qgis python-qgis \
                   saga python-saga && \
    apt clean all

ARG uid=1000
RUN useradd -m -u $uid builder

USER builder

WORKDIR /io

ENV DISPLAY=:99
ENV PYTHONPATH=/io

ENTRYPOINT ["/bin/bash", "/io/docker/run_make.sh"]
