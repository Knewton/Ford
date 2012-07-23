#!/bin/bash
BSOUP_URL="http://www.crummy.com/software/BeautifulSoup/bs4/download/4.0/beautifulsoup4-4.1.0.tar.gz"

python -c "import BeautifulSoup" > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
	echo "Installing BeautifulSoup"
	cd /tmp/
	rm -rf beautifulsoup*
	curl --silent --output beautifulsoup.tar.gz $BSOUP_URL
	ls beautifulsoup.tar.gz
	tar -xvzf beautifulsoup.tar.gz
	rm beautifulsoup.tar.gz
	cd beautifulsoup*
	sudo python setup.py install
fi
