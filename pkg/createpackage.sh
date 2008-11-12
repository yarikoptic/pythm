#!/bin/sh

rm -rf tmp


cd ..
rm -rf build
python setup.py bdist
cd pkg

mkdir tmp
mkdir tmp/CONTROL
cp control tmp/CONTROL

#tar contents into pkg dir
tar -C tmp -xvzf ../dist/Pythm*i686.tar.gz

chown -R root:root tmp

#make ipk
./ipkg-build.sh tmp

rm -rf tmp

