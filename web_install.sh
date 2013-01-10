#!/bin/sh

# Location of the Ford archive
zip_url="https://nodeload.github.com/Knewton/Ford/zip/master"
ford_dir="ford$(date +%s)"
ford_log="/tmp/$ford_dir.log"

# Location of Ford install
ford_path=`which ford`
has_ford=$?

# Determine if the system already has ford installed
if [[ $has_ford -eq 0 ]]; then
	echo "Ford already installed"

	echo ""
	ford -h

	exit 0
fi

# Setup the workspace
cd /tmp
mkdir $ford_dir
cd $ford_dir

# Get the zip and enter the directory
echo "Downloading Ford ($zip_url)..." | tee -a $ford_log
curl -vso ford.zip "$zip_url" >> $ford_log 2>&1
unzip ford.zip >> $ford_log 2>&1
cd Ford-master

# Install the dependencies
echo "Installing dependencies..." | tee -a $ford_log
echo "NOTE: You may be prompted for your password for sudo installs."
./bin/install_dependencies.sh >> $ford_log 2>&1

# Install ford
echo "Installing Ford..." | tee -a $ford_log
sudo python setup.py install >> $ford_log 2>&1

# Test install
ford_path=`which ford`
has_ford=$?

# Setup ford
if [[ $has_ford -eq 0 ]]; then
	echo "Ford installed successfully; setting up..." | tee -a $ford_log
	ford upgrade >> $ford_log 2>&1
	ford import -f >> $ford_log 2>&1
else
	echo "Error installing ford. Check $ford_log for details."
	exit 1
fi

# Remove the dir
echo "Cleaning up..." | tee -a $ford_log
cd /tmp
sudo rm -rf $ford_dir # Need sudo again to remove the directory

# Display help
echo "Ford installation complete." | tee -a $ford_log
echo "Check $ford_log for details."

echo ""
ford -h

