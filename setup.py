#! /usr/bin/env python

from distutils.core import setup
from os import environ, mkdir, symlink
from os.path import expanduser, isdir
from distutils.sysconfig import get_python_lib

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
			"templates/*/*",
			"manifests/*",
			"scripts/*"
		]
	},
	data_files=[
		("/usr/local/bin", ["bin/ford"])
	]
)
