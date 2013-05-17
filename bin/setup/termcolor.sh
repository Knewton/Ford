#!/usr/bin/env bash
SRC="https://pypi.python.org/packages/source/t/termcolor/termcolor-1.1.0.tar.gz"

python -c "import termcolor" > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
	echo "Installing termcolor"
	cd /tmp/
	rm -rf termcolor*
	curl --silent --output termcolor.tar.gz $SRC
	ls termcolor.tar.gz
	tar -xvzf termcolor.tar.gz
	rm termcolor.tar.gz
	cd termcolor*
	sudo python setup.py install
	cd ..
	sudo rm -rf termcolor*
fi

