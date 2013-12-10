#!/usr/bin/env bash
function gem_install {
	gem_name="$1"
	if [[ -z `gem list | grep $gem_name` ]]; then
		echo "INSTALL: gem: $gem_name."
		sudo gem install $gem_name
	fi
}

#	Sanity check
which gem > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
	echo "ERROR: 'gem' missing; install 'gem' to continue."
	exit 1
fi

gem_install compass
