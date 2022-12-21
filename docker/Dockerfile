# vi:syntax=dockerfile
FROM debian:bullseye
MAINTAINER GEM Foundation <devops@openquake.org>
#  ovveride the value with --build-arg uid=$(id -u)
ARG uid=1001

ENV DEBIAN_FRONTEND noninteractive

RUN apt update && apt full-upgrade -y && apt -q install -y gnupg2 \
				   wget locales build-essential git sudo xvfb zip \
				   qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools \	
                   pyqt5-dev pyqt5-dev-tools \
                   python3-pyqt5.qtwebkit python3-pip \
                   python3-mock python3-nose \
                   python3-nose-exclude python3-scipy \
                   ghostscript \
                   texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended && \
    pip3 install sphinx==1.4.9 sphinx_rtd_theme && \
    locale-gen en_US.UTF-8
#
COPY qgis.sources /etc/apt/sources.list.d/
#
RUN mkdir -m755 -p /etc/apt/keyrings && wget -O /etc/apt/keyrings/qgis-archive-keyring.gpg https://download.qgis.org/downloads/qgis-archive-keyring.gpg && \
	apt update && \
    apt install -y qgis python-qgis && \
    apt clean all
RUN echo uid $uid && useradd -m -u $uid builder && \
    echo 'builder ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER builder
ADD gitconfig /home/builder/.gitconfig

WORKDIR /io

ENV LANG en_US.UTF-8
ENV DISPLAY=:99
ENV PYTHONPATH=/io
ENV PYTHONIOENCODING=utf_8

ENTRYPOINT ["/bin/bash", "/io/docker/run_make.sh"]
