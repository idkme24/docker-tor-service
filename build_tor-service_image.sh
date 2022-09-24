#!/bin/bash

TOR_VERSION='0.4.7.10'
BUILD_DIR=/tmp
PROJECT_DIR=$(pwd)

echo "Installing Dependencies"
dnf install wget libevent-devel.x86_64 openssl-devel.x86_64 zlib-devel.x86_64 xz-devel.x86_64 libzstd-devel.x86_64 make gcc -y

echo "Downloading Tor Source"
cd $BUILD_DIR
wget https://dist.torproject.org/tor-$TOR_VERSION.tar.gz $BUILD_DIR

if [ -d "$BUILD_DIR/tor-$TOR_VERSION" ]; then
	rm -rf $BUILD_DIR/tor-$TOR_VERSION
fi
tar -xzf tor-$TOR_VERSION.tar.gz

echo "Configure Source"
cd $BUILD_DIR/tor-$TOR_VERSION
./configure

echo "Make Source"
make

echo "Collect Tor executable and torrc.sample"
cp $BUILD_DIR/tor-$TOR_VERSION/src/app/tor $PROJECT_DIR/tor
cp $BUILD_DIR/tor-$TOR_VERSION/src/config/torrc.sample $PROJECT_DIR/torrc

echo "Build Docker image"
cd $PROJECT_DIR

docker build -t tor-service .
