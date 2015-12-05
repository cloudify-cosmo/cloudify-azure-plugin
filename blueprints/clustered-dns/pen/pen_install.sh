#! /bin/bash

echo "The script for installing and configurig PEN starts now!"

yum install -y automake autoconf gcc git
mkdir Git
cd Git
git clone https://github.com/UlricE/pen.git
cd pen
aclocal
automake --add-missing
autoconf
./configure
make
