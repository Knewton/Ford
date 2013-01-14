#!/bin/sh

# Based on https://npmjs.org/install.sh
# A word about this shell script:
#
# It must work everywhere, including on systems that lack
# a /bin/bash, map 'sh' to ksh, ksh97, bash, ash, or zsh,
# and potentially have either a posix shell or bourne
# shell living at /bin/sh.
#
# See this helpful document on writing portable shell scripts:
# http://www.gnu.org/s/hello/manual/autoconf/Portable-Shell.html
#
# The only shell it won't ever work on is cmd.exe.

#------------------------------
#
# Configurations
#
#------------------------------

#------------------------------
# About: required
#------------------------------

# The permanant web URL of the most up-to-date raw text version of this script.
wi_uri="https://raw.github.com/Knewton/Ford/master/web_install.sh"

# The name of your software.
wi_name="Ford"

# The copyright years and holder, without the (c) which is added when displayed
wi_copyright="2012 Knewton"

# The license name and a URL to the license text
wi_license="MIT: http://opensource.org/licenses/MIT"

#------------------------------
# About: optional
#------------------------------

# A description of your software.
wi_desc="A web application dependency management and development tool."

# How to display usage instructions for the software. Leave blank for none.
wi_usage="ford -h"

# Human readable website about the software (github URL, etc)
wi_url="https://github.com/Knewton/Ford"

# The authors of the software
wi_authors="Eric Garside"

#------------------------------
# Software packages
#------------------------------

# The URL of the ford zip archive
ford_zip="https://nodeload.github.com/Knewton/Ford/zip/master"

#------------------------------
#
# Abstract Methods
#
#------------------------------

#------------------------------
# Testing
#------------------------------

# Determine if your software is already installed.
# @ret 0 - Yes; 1 - No; 2 - Yes, but nees update
IsSoftwareInstalled() {
	ProgramExists "ford" ; ford_installed=$?

	if [ $ford_installed -eq 0 ]; then
		# By default, return that we need an upgrade anytime the installer is
		# run. In the future, this can probably be enhanced with a version
		# checker, but Ford has no such capability right now
		return 2
		# if [ behind_current_version ]; then
		# 	return 2
		# else
		# 	return 0
		# fi
	fi

	# Not installed
	return 1
}

# Determine if the software can be installed (check dependenceis, etc).
# @ret 0 - Yes; 1 - No
CanInstallSoftware() {
	ret=0

	ProgramExists "python" ; python_installed=$?
	ProgramExists "gem" ; gem_installed=$?
	ProgramExists "java" ; java_installed=$?

	# Can BeautifulSoup be installed?
	if [ $python_installed -eq 1 ]; then
		Log "No version of python detected; install Python 2.6+ and retry."
		ret=1
	fi

	# Can Juicer be installed?
	if [ $gem_installed -eq 1 ]; then
		Log "No version of Ruby Gem detected; install Ruby and Gem and retry."
		ret=1
	fi

	# Can YUICompressor, used in Juicer, be installed?
	if [ $java_installed -eq 1 ]; then
		Log "No version of java detected; install Java and retry."
		ret=1
	fi

	return $ret
}

#------------------------------
# Actions
#------------------------------

# All actions use the same return signals
# Ret: 0 - Everything went fine; 1 - Something went wrong

# Whatever needs to be done to install the software the first time.
InstallSoftware() {
	ret=0

	Fetch "$ford_zip" "ford.zip" ; got_pkg=$?
	if [ $got_pkg -eq 0 ]; then
		Capture unzip ford.zip ; did_unzip=$?
		if [ $did_unzip -eq 0 ]; then
			# Enter the ford directory
			cd Ford-master/

			Log "Installing dependencies (may take a while)..."
			SubSudoNotice
			Capture ./bin/install_dependencies.sh

			Log "Installing Ford..."
			SudoPrompt python setup.py install

			# Return to the workspace when done
			cd $_wi_workspace
		else
			ret=1
			Log "Failed to unzip ford archive."
		fi
	else
		ret=1
		Log "Failed to download ford archive."
	fi

	return $ret
}

# Any tasks which need to be done once the install has completed.
PostInstall() {
	Capture ford upgrade
	Capture ford import -f

	return 0
}

# Whatever needs to be done to update the software
UpdateSoftware() {
	Capture ford upgrade
	Capture ford import -f

	return 0
}

################################## Internal ###################################

#------------------------------
#
# Congfigurations
#
#------------------------------

#------------------------------
# Installation
#------------------------------

# This is the exit code for this script
_wi_status=0

# If the software is already installed
_wi_installed=-1

# The action to take
_wi_action=""

# Has the user confirmed the requested action
_wi_confirmed=1

# Directory to return to after install
_wi_return_to="$PWD"

# The workspace for the install
_wi_workspace="${TMPDIR}"
if [ "x$_wi_workspace" = "x" ]; then
	_wi_workspace="/tmp"
fi
_wi_workspace="$_wi_workspace/$wi_name.web_install.$$"

#------------------------------
# Logging
#------------------------------

# Place the log in the current directory
_wi_logpath="$PWD/$wi_name.web_install.$(date +%m-%d-%Y.%H-%M-%S)"

#------------------------------
#
# Utility Methods
#
#------------------------------

#------------------------------
# Helpers
#------------------------------

# Determines if the provided prog exists on the path
# @arg string name The name of the program to check.
# @ret 0 - Program exists; 1 - Program not found
ProgramExists() {
	pathto=`which $1 2>&1`
	ret=$?
	if [ $ret -ne 0 ] || ! [ -x "$pathto" ]; then
		return 1
	fi

	return 0
}

# Simple notice that a subshell may requires sudo permissions
SubSudoNotice() {
	echo "Installing dependencies which may require sudo..."
}

# Fetch a file from a URI.
# @arg string uri The file to get.
# @arg string as The name to save as.
# @ret The return code of the curl
Fetch() {
	Log "Fetching $1..."
	Capture curl -vso "$2" "$1"
	return $?
}

#------------------------------
# Wrappers
#------------------------------

# Echo a message to stdout append it to the log
# @arg string msg
Log() {
	echo "$1" | tee -a "$_wi_logpath"
}

# Execution wrapper which redirects all output to the log, hiding from stdout.
# @arg string prog The name of the program the execute
# @arg ... args The arguments for the program
# @ret The return code of the captured program
Capture() {
	op=$1 ; shift
	$op "$@" >> "$_wi_logpath" 2>&1
	return $?
}

# Execution wrapper which alerts user to use of sudo and why; captures output.
# @arg string prog The name of the program the execute
# @arg ... args The arguments for the program
# @ret The return code of the captured program
SudoPrompt() {
	echo "sudo $@"
	op=$1 ; shift
	sudo $op "$@" >> "$_wi_logpath" 2>&1
	return $?
}

#------------------------------
# Methods
#------------------------------

# Creates a directory for the installer, then changes into it.
# @ret 0 - Created; 1 - Failed
CreateWorkspace() {
	if [ -d $_wi_workspace ]; then
		Log "The workspace '$wi_workspace' exists and must be removed."
		# Some directories may sudo install; so sudo remove
		SudoPrompt rm -rf "$_wi_workspace"
	fi

	Capture mkdir -p "$_wi_workspace"
	if [ $? -ne 0 ]; then
		Log "Failed to create workspace $_wi_workspace"
		return 1
	fi

	cd "$_wi_workspace"

	return 0
}

# Removes the workspace and returns to the old directory
DestroyWorkspace() {
	if [ -d $_wi_workspace ]; then
		echo "Cleaning up..."
		# Some directories may sudo install; so sudo remove
		SudoPrompt rm -rf "$_wi_workspace"
	fi

	cd "$_wi_return_to"
}

# Displays and logs information about the software being managed.
DisplaySoftwareInformation() {
	disp_name="$wi_name"
	if [ -n "$wi_url" ]; then
		disp_name="$disp_name ($wi_url)"
	fi

	Log "$disp_name"
	if [ -n "$wi_desc" ]; then
		Log "  $wi_desc"
	fi

	Log "Copyright (c) $wi_copyright"

	if [ -n "$wi_authors" ]; then
		Log "  Authors: $wi_authors"
	fi

	Log "Licensed under:"
	if [ -z "$wi_license" ]; then
		wi_license="Unknown: No license provided."
	fi
	Log "  $wi_license"
}

# Displays information to the user and gains explicit permission to continue
# @ret 0 - Continue; 1 - Stop.
ConfirmInstall() {
	echo "The following software is requesting permission to $_wi_action:\n"

	DisplaySoftwareInformation

	printf "\nContinue with $wi_name $_wi_action? [Y/n]: "
	read user_confirmation < /dev/tty

	if [ "$user_confirmation" = "n" ]; then
		return 1
	fi

	return 0
}

#------------------------------
#
# Installation
#
#------------------------------

#------------------------------
# curl | sh handler
#------------------------------

if [ "x$0" = "xsh" ]; then
	# run as curl | sh
	# on some systems, you can just do cat > web_install.sh
	# which is a bit cuter.  But on others, &1 is already closed,
	# so catting to another script file won't do anything.
	# This is triggered when users do `cat web_install.sh | sh`
	curl -s $wi_uri > web_install-$$.sh
	sh web_install-$$.sh
	ret=$?
	rm web_install-$$.sh
	exit $ret
fi

#------------------------------
# Software Installation
#------------------------------

# Does anything need to happen?
IsSoftwareInstalled ; _wi_installed=$?
case $_wi_installed in
	0) echo "$wi_name is already installed." ;;
	1) _wi_action="install" ;;
	2) _wi_action="update" ;;
esac

# Perform the installation actions as described
if [ -n "$_wi_action" ]; then
	ConfirmInstall ; _wi_confirmed=$?
	if [ $_wi_confirmed -eq 0 ]; then
		CreateWorkspace ; has_workspace=$?
		if [ $has_workspace -eq 0 ]; then
			echo ""
			case $_wi_action in
				"install")
					Log "Testing environment..."
					CanInstallSoftware ; can_install=$?

					if [ $can_install -eq 0 ]; then
						Log "Installing..."
						InstallSoftware ; _wi_status=$?
					else
						_wi_status=1
					fi

					# If the status is still clear...
					if [ $_wi_status -eq 0 ]; then
						# Check to make sure we now pass our install test...
						IsSoftwareInstalled ; _wi_installed=$?
						if [ $_wi_installed -ne 1 ]; then
							# Anything other than a fresh install is a success
							PostInstall ; _wi_status=$?
						fi
					fi
					;;

				"update")
					Log "Updating..."
					UpdateSoftware ; _wi_status=$?
					;;
			esac

			DestroyWorkspace
		fi
	else
		echo "Aborted."
		rm $_wi_logpath
	fi
fi

#------------------------------
# Exit
#------------------------------

if [ -f $_wi_logpath ]; then
	echo "\nA log of this installation is available here: $_wi_logpath"
fi

if [ $_wi_installed -ne 1 ]; then
	if [ -n "$wi_usage" ]; then
		echo "\nUsage instructions: $wi_usage\n"
		`$wi_usage`
	fi
fi

exit $_wi_status

