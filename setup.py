#!/usr/bin/env python
from setuptools import setup

setup(
	name="ford",
	version = "0.1",
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
	scripts = [
		"bin/ford",
		"bin/ssl_server_ford",
		"bin/server_ford",
	],
	install_requires = [
		"BeautifulSoup==3.2.0",
		"termcolor==1.1.0",
		"Jinja2==2.7.0",
		"CoffeeScript==1.0.5",
#		"pyOpenSSL==0.13",
	]
)

