#!/usr/bin/env bash

# MacOSX ruins everything by not coming packaged with OpenSSL headers. Using
# easy_install is the only known way to get OpenSSL on MacOSX

python -c "import OpenSSL" > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
	echo "Installing OpenSSL"
	sudo easy_install PyOpenSSL
fi
