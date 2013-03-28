#!/usr/bin/env python
from optparse import OptionParser
from os.path import abspath, isdir
from os import chdir
from sys import exit
from ford.utilities import mkdirp

from ford.project import Project, upgrade, cdnimport

SUPPORTED_ACTIONS = ["upgrade", "init", "update", "build"]

def optparse():
	desc="\n".join(["usage: %prog [options] action [directory]",
			"A development and build tool for javascript applications.",
			"",
			"Supported actions:",
			"    import:  Pulls in all the packages hosted on CDNJS as ford",
			"             ready manifests for import. Use --force to update",
			"             the cached package listing from cdnjs.com",
			"    upgrade: Upgrades the current user's ford resources.",
			"             Use --force to overwrite existing resources.",
			"    init:    Copies project resources from a template.",
			"             Use --force to overwrite existing resources.",
			"             Use --template to specify a new template.",
			"    update:  Updates external resources. Runs init first.",
			"             Use --skip to skip init resource before build.",
			"    build:   Builds the project. Runs init and update first.",
			"             Use --skip to skip init and update before build.",
			"             Use --output to change build directory.",
			"    embed:   Embeds all files into the index.html to make a one",
			"             page application. You can enable this by setting",
			"             'embed': true in manifest.json.",
			"    rawsrc:  Does not minify javascript files. You can enable ",
			"             this by setting 'rawsrc': true in manifest.json.",
	])
	parser = OptionParser(usage=desc)
	parser.add_option("-f", "--force", dest="force", action="store_true",
						default=False, help="Force overwrites.")
	parser.add_option("-s", "--skip", dest="skip", action="store_true",
						default=False, help="Builds without upgrading.")
	parser.add_option("-t", "--template", dest="template",
						help="The project template to use for init.")
	parser.add_option("-o", "--output", dest="output", default="./output",
						help="The directory to output built files to.")
	parser.add_option("-e", "--embed", dest="embed", action="store_true",
						default=False, help="Embed into one index.html file.")
	parser.add_option("-r", "--rawsrc", dest="rawsrc", action="store_true",
						default=False, help="Do not minify javascript.")
	return parser

def main():
	opts, args = optparse().parse_args()

	action, directory = "help", "."

	if len(args) >= 2:
		action = args[0]
		d = args[1]
		if not isdir(d):
			mkdirp(d)
		chdir(d)
	elif len(args) == 1:
		action = args[0]

	directory = abspath(directory)
	if action == "help":
		optparse().print_help()
		exit(0)
	elif action == "upgrade":
		upgrade(opts.force)
		exit(0)
	elif action == "import":
		cdnimport(opts.force)
		exit(0)

	if not action in SUPPORTED_ACTIONS:
		print "action must be '{0}'; '{1}' is not supported".format(
			", ".join(SUPPORTED_ACTIONS), action)
		exit(0)

	p = Project(directory)
	if not opts.skip or action == "init":
		if not p.init(opts.template, opts.force, action == "init"):
			exit(1)

	if action == "init":
		exit(0)

	if action == "update":
		p.update()
	else:
		p.build(abspath(opts.output), opts.skip, opts.embed, opts.rawsrc)

	exit(0)

if __name__ == "__main__":
	main()
