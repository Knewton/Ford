#!/usr/bin/env bash
BSOUP_URL="http://pypi.python.org/packages/source/B/BeautifulSoup/BeautifulSoup-3.2.1.tar.gz"

python -c "import BeautifulSoup" > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
	echo "Installing BeautifulSoup"
	cd /tmp/
	rm -rf beautifulsoup*
	rm -rf BeautifulSoup*
	curl --silent --output beautifulsoup.tar.gz $BSOUP_URL
	ls beautifulsoup.tar.gz
	tar -xvzf beautifulsoup.tar.gz
	rm beautifulsoup.tar.gz
	cd BeautifulSoup*
	sudo python setup.py install
fi
