#!/usr/bin/env bash
SRC="http://pypi.python.org/packages/source/B/BeautifulSoup/BeautifulSoup-3.2.0.tar.gz"

python -c "import BeautifulSoup" > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
	echo "Installing BeautifulSoup"
	cd /tmp/
	rm -rf beautifulsoup*
	sudo rm -rf BeautifulSoup*
	curl --silent --output beautifulsoup.tar.gz $SRC
	ls beautifulsoup.tar.gz
	tar -xvzf beautifulsoup.tar.gz
	rm beautifulsoup.tar.gz
	cd BeautifulSoup*
	sudo python setup.py install
	cd ..
	sudo rm -rf BeautifulSoup*
fi
