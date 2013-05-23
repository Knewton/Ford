#! /usr/bin/env python

from distutils.core import setup
from os import environ, mkdir, symlink
from os.path import expanduser, isdir
from distutils.sysconfig import get_python_lib

def get_version():
	"""build_version is replaced with the current build number
	as part of the jenkins build job"""
	build_version = 1
	return build_version

setup(
	name="ford",
	description="A development and build tool for javascript applications.",
	author="Eric Garside",
	author_email="eric@knewton.com",
	url="http://github.com/Knewton/Ford",
	packages = ["ford"],
	platforms=["any"],
	package_data={
		"ford": [
			"scripts/*"
		]
	},
	data_files=[
		("/usr/local/bin", ["bin/ford"])
	]
)
