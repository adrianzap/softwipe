FROM ubuntu:20.04

LABEL maintainer="Bernd Doser <bernd.doser@h-its.org>"

ARG TIMEZONE='Europe/Berlin'
ARG DEBIAN_FRONTEND=noninteractive

RUN echo $TIMEZONE > /etc/timezone \
 && apt-get update \
 && apt-get install -y tzdata \
 && rm /etc/localtime \
 && ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime \
 && dpkg-reconfigure -f noninteractive tzdata \
 && apt-get clean

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    ca-certificates \
    cmake \
    cppcheck \
    curl \
    dirmngr \
    git \
    git-svn \
    gpg-agent \
    kwstyle \
    make \
    ninja-build \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-tk \
    software-properties-common \
    vim \
    wget

RUN wget -q -O - http://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add - \
 && CODENAME=$(lsb_release -cs) \
 && echo "deb http://apt.llvm.org/$CODENAME/ llvm-toolchain-$CODENAME-11 main" >> /etc/apt/sources.list \
 && echo "deb-src http://apt.llvm.org/$CODENAME/ llvm-toolchain-$CODENAME-11 main" >> /etc/apt/sources.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
    clang-tidy \
    clang-11 \
    clang-11-doc \
    clang-format-11 \
    clangd-11 \
    libc++-11-dev \
    libc++abi-11-dev \
    libomp-11-dev \
    libllvm-11-ocaml-dev \
    libclang-11-dev \
    libclang-common-11-dev \
    libclang1-11 \
    libfuzzer-11-dev \
    libllvm11 \
    lld-11 \
    lldb-11 \
    llvm-11 \
    llvm-11-dev \
    llvm-11-doc \
    llvm-11-examples \
    llvm-11-runtime \
    python3-clang-11 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && update-alternatives --install /usr/bin/clang clang /usr/bin/clang-11 100 \
 && update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-11 100

ENV CC clang
ENV CXX clang++

RUN pip install --upgrade pip \
 && hash -r pip3 \
 && pip install \
    compiledb \
    lizard \
    numpy \
    scipy

RUN git clone https://github.com/adrianzap/softwipe.git \
 && cd softwipe \
 && git clone https://github.com/Kitware/KWStyle.git \
 && cd KWStyle \
 && mkdir build \
 && cd build \
 && cmake .. \
 && make

RUN /softwipe/softwipe.py -h
ENV PATH="/softwipe:${PATH}"
