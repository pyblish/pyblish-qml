#!/bin/bash

echo "Building in $TRAVIS_OS_NAME"

echo "Fetching data.."
wget http://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.5.1/PyQt-gpl-5.5.1.tar.gz
wget http://sourceforge.net/projects/pyqt/files/sip/sip-4.17/sip-4.17.tar.gz

echo "Building sip.."
tar xvzf sip-4.17.tar.gz
cd sip-4.17
python configure.py
make
sudo make install
cd ..

echo "Building PyQt5.."
tar xvzf PyQt-gpl-5.5.1.tar.gz
cd PyQt-gpl-5.5.1
python configure.py --sip=$SIP --confirm-license
make
sudo make install
cd ..

echo "Finished install.sh"