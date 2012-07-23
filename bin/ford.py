#!/usr/bin/env python
from optparse import OptionParser
from os.path import abspath, isdir
from sys import exit

from ford.project import Project, upgrade

SUPPORTED_ACTIONS = ["upgrade", "init", "update", "build"]

def optparse():
	desc="\n".join(["usage: %prog [options] action [directory]",
			"A development and build tool for javascript applications.",
			"",
			"Supported actions:",
			"    upgrade: Upgrades the current user's ford resources.",
			"             Use --force to overwrite existing resources.",
			"    init:    Copies project resources from a template.",
			"             Use --force to overwrite existing resources.",
			"             Use --template to specify a new template.",
			"    update:  Updates external resources. Runs init first.",
			"             Use --skip to skip init resource before build.",
			"    build:   Builds the project. Runs init and update first.",
			"             Use --skip to skip init and update before build.",
			"             Use --output to change build directory."
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
	return parser

def main():
	opts, args = optparse().parse_args()

	action, directory = "help", "."

	if len(args) >= 2:
		action = args[0]
		directory = args[1]
	elif len(args) == 1:
		action = args[0]

	directory = abspath(directory)
	if action == "help":
		optparse().print_help()
		exit(0)
	elif action == "upgrade":
		upgrade(opts.force)
		exit(0)

	if not action in SUPPORTED_ACTIONS:
		print "action must be '{0}'; '{1}' is not supported".format(
			", ".join(SUPPORTED_ACTIONS), action)
		exit(0)

	p = Project(directory)
	if not opts.skip or action != "init":
		p.init(opts.template, opts.force)

	if action == "init":
		exit(0)

	if action == "update":
		p.update()
	else:
		p.build(abspath(opts.output), opts.skip)

	exit(0)

if __name__ == "__main__":
	main()
