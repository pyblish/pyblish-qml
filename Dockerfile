# Usage:
#
# cd pyblish-qml
# docker run --rm -v $(pwd):/pyblish-qml pyblish/pyblish-qml


FROM ubuntu:14.04

MAINTAINER marcus@abstractfactory.io

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    python3-pyqt5 \
    python3-pyqt5.qtquick \
    python3-pip \
    python3-nose && \
    pip3 install \
        nose \
        coverage

RUN mkdir /deps && cd /deps && \
    git clone https://github.com/pyblish/pyblish-rpc && \
    git clone https://github.com/pyblish/pyblish-base

ENV PYTHONPATH=/deps/pyblish-rpc:/deps/pyblish-base

WORKDIR /pyblish-qml
ENTRYPOINT python3 run_testsuite.py
