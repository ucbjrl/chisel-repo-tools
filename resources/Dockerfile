# syntax=docker/dockerfile:1
FROM ubuntu:20.04

RUN apt-get update

# DEBIAN_FRONTEND=noninteractive suppresses interactive localization questions
# See https://askubuntu.com/questions/909277
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
  curl \
  cvc4 \
  gawk \
  gnupg2 \
  iverilog \
  openjdk-11-jdk \
  python3 \
  python3-pip \
  python3-venv \
  tar \
  vim \
  wget

WORKDIR /opt

# Get oss-cad-suite for newer verilator
RUN wget https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2022-02-07/oss-cad-suite-linux-x64-20220207.tgz

RUN tar zxvf oss-cad-suite-linux-x64-20220207.tgz

# Put after the normal path because we want iverilog from package manager to win
# For some reason, the iverilog from oss-cad-suite doesn't seem to work right
ENV PATH="$PATH:/opt/oss-cad-suite/bin"

# Download firtool
RUN mkdir -p circt

RUN wget https://github.com/llvm/circt/releases/download/firtool-1.37.0/firrtl-bin-ubuntu-20.04.tar.gz -O - | tar -zx -C circt/ --strip-components 1

ENV PATH="$PATH:/opt/circt/bin"

# Add SBT repo
RUN echo "deb https://repo.scala-sbt.org/scalasbt/debian all main" | tee /etc/apt/sources.list.d/sbt.list && \
  echo "deb https://repo.scala-sbt.org/scalasbt/debian /" | tee /etc/apt/sources.list.d/sbt_old.list && \
  curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | apt-key add

# Install SBT
RUN apt-get update && apt-get install -y \
  sbt

COPY resources/publish_plugins.sbt /root/.sbt/1.0/plugins/publish.sbt

WORKDIR /work

COPY . chisel-repo-tools/

WORKDIR /work/chisel-repo-tools/

RUN pip3 install -r resources/requirements.txt

WORKDIR /work

