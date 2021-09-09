# syntax=docker/dockerfile:1
FROM ubuntu:20.04

# DEBIAN_FRONTEND=noninteractive suppresses interactive localization questions
# See https://askubuntu.com/questions/909277
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
  curl \
  gawk \
  gnupg2 \
  openjdk-11-jdk \
  python3 \
  python3-pip \
  python3-venv \
  verilator \
  vim \
  yosys \
  z3

# Add SBT repo
RUN echo "deb https://repo.scala-sbt.org/scalasbt/debian all main" | tee /etc/apt/sources.list.d/sbt.list && \
  echo "deb https://repo.scala-sbt.org/scalasbt/debian /" | tee /etc/apt/sources.list.d/sbt_old.list && \
  curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | apt-key add

# Install SBT
RUN apt-get update && apt-get install -y \
  sbt

WORKDIR /work

COPY . chisel-repo-tools/

WORKDIR /work/chisel-repo-tools/

RUN pip3 install -r resources/requirements.txt

WORKDIR /work

