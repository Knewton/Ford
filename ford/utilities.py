#!/usr/bin/env python
from os.path import (expanduser, isdir, exists, join, abspath, splitext,
	basename, dirname)
from os import mkdir, makedirs, listdir
from errno import EEXIST
from subprocess import Popen, PIPE, STDOUT
from types import ListType
from shutil import copyfile
from pprint import pprint, pformat
from termcolor import colored, cprint

def mkdirp(path):
	try:
		makedirs(path)
	except OSError as exc: # Python >2.5
		if exc.errno == EEXIST:
			pass
		else: raise

def read_file(file_path):
	with open(file_path, 'r') as f:
		data = f.read()
	return data

def write_file(file_path, content, mode="w"):
	with open(file_path, mode) as stream:
		stream.write(content)

def call(cmd, failexit=False, output=False, failout=False, tab=False):
	if type(cmd) == ListType:
		cmd = " ".join(cmd)
	process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=True)
	out = process.communicate()[0]
	if output:
		print out
	code = process.returncode
	if code != 0:
		if failout:
			print out
		if failexit:
			exit(code)
	return code

def fix_path(p):
	return abspath(expanduser(p))

def copy_missing_files(src, dest, force, underscore=False):
	if not isdir(dest):
		mkdir(dest)

	had_file = False
	for f in listdir(src):
		fp = join(src, f)

		# Replace underscore with dot
		if underscore and f[0] == "_":
			dest_fp = join(dest, ".{0}".format(f[1:]))
		else:
			dest_fp = join(dest, f)

		if isdir(fp):
			if copy_missing_files(fp, join(dest, f), force, underscore):
				had_file = True
		else:
			act = "add"
			if exists(dest_fp):
				if not force:
					continue
				else:
					act = "overwrite"
			print_event(act, fp, dest_fp)
			copyfile(fp, dest_fp)
			had_file = True
	return had_file

def merge_directories(src, dest, dirs=None, force=False, underscore=False):
	src = fix_path(src)
	dest = fix_path(dest)
	made_change = False

	if not isdir(src):
		return False

	if not isdir(dest):
		mkdir(dest)

	if dirs is None:
		return copy_missing_files(src, dest, force, underscore)

	for d in dirs:
		if copy_missing_files(join(src, d), join(dest, d), force, underscore):
			made_change = True
	return made_change

def create_archive_basedir(file_path):
	"""Given an archive, creates a sibling directory for clean checkout"""
	file_name, ext = splitext(basename(file_path))
	basedir = join(dirname(file_path), file_name)

	if not isdir(basedir):
		makedirs(basedir)

	return basedir

def unzip(archive, path):
	from zipfile import ZipFile
	z = ZipFile(archive, "r")
	z.extractall(path)

def untar(archive, path):
	from tarfile import TarFile
	t = TarFile(archive, "r")
	t.extractall(path)

class UnknownArchiveException(Exception):
	pass

def unpackage(file_path, package_type=None):
	"""Unpackages an archive into a sibling directory of the same name."""
	if package_type is None:
		if ".tar" in file_path:
			package_type = "tar"
		else:
			file_name, ext = splitext(file_path) # foo.txt -> (foo, .txt)
			package_type = ext[1:] # Remove the . from .txt

	# Create a sibling directory for extraction
	basedir = create_archive_basedir(file_path)

	# Handle the extraction
	if package_type == "zip":
		unzip(file_path, basedir)
		print_event("unzip", file_path, basedir)
	elif package_type == "tar":
		untar(file_path, basedir)
		print_event("untar", file_path, basedir)
	else:
		raise UnknownArchiveException(package_type)

	# Return the destination
	return basedir

#------------------------------
#
# Output control
#
#------------------------------

loc = {
	"action": {
		"selfupdate": "Ford System Update",
		"upgrade": "Ford System Upgrade",
		"import": "Ford Project Import",
		"init": "Ford Project Initialization [{0}]",
		"build": "Ford Project Build [{0}]",
		"update": "Ford Project Update [{0}]"
	},
	"notice": {
		"import": {
			"nothing": "[SUCCESS] No files to import."
		},
		"upgrade": {
			"nothing": "[SUCCESS] No files to upgrade."
		},
		"init": {
			"nothing": "[SUCCESS] No initialization tasks."
		}
	},
	"success": {
		"selfupdate": "[SUCCESS] An update log is available here: {0}",
		"upgrade": "[SUCCESS] The upgrade process finished successfully.",
		"import": "[SUCCESS] The import process finished successfully.",
		"compiling": "[COMPILE] {0:<80}",
		"application": "[  APP  ] {0:<80}",
		"build": "[ BUILD ] Project built successfully!",
		"lib": "[  LIB  ] {0:<80}",
	},
	"warning": {
		"compiling": "[FULLSRC] {0:<80}",
	},
	"alert": {
		"sudo": "NOTICE! You are being asked for your password to enable sudo for updating Ford."
	},
	"exception": {
		"compiling": "[COMPILE] {0:<80}",
		"selfupdate": "[ ERROR ] An error log is available here: {0}",
		"missing_file": "[MISSING] {0:<80}",
		"missing_dir": "[ NODIR ] {0:<80}",
		"missing_property": "[  KEY  ] {0} does not appear in {1}",
		"missing_template": "[MISSING] ~/.ford/templates/{0:<62}", # 62 = 80 - len(~/.ford/templates/)
		"missing_tag": '[ NOTAG ] {1} must contain a tag with id="{0}"',
		"missing_lib": "[ NOLIB ] {0} is not a valid library",
		"bad_comp": "[INVALID] {0} {1} has invalid composition {{0}}",
		"missing_resource": "[MISSING] {1} does not contain {0}",
		"invalid_file": "[INVALID] {1:<80} File is not {0}",
		"invalid_mime": "[INVALID] {1:<80} File is not of mime-type {0}",
		"not_project": "[INVALID] {0:<80} Is not a project. Try ford init?",
		"resource": "[ ERROR ] {0} {1}",
		"copying": "[COPYING] {0:<80} {1}",
		"http": "[HTTPERR] {1:<80} {0}"
	},
	"compiling": "[ BEGIN ] {0:<80}",
	"embed": "[ EMBED ] {0:<80} {1:<80}",
	"overwrite": "[ FORCE ] {0:<80} {1:<80}",
	"untar": "[ UNTAR ] {0:<80} {1:<80}",
	"unzip": "[ UNZIP ] {0:<80} {1:<80}",
	"add": "[ MOVED ] {0:<80} {1:<80}",
	"wget": "[ FETCH ] {0:<80} {1:<80}",
	"clone": "[ CLONE ] {0:<80} {1:<80}",
	"full_lib": "[LIBRARY] {0:<80} {1:<80}",
	"import": "[IMPORT] {0:<80} Version {1}",
	"parts": "[ PARTS ] {0:<80}",
	"ignored": "[CUT OUT] {0:<80}",
	"created": "[ MKDIR ] {0:<80}",
	"removed": "[REMOVED] {0:<80}",
	"symlink": "[SYMLINK] {0:<80} {1:<80}"
}

USR_PATH = expanduser("~")
PDIR = None
def shrt(path):
	o = path.replace(USR_PATH, "~")
	if PDIR is not None:
		o = o.replace(PDIR, ".")
	return o

def clprint(msg, *args, **kwargs):
	print msg

USE_COLOR = True
FIRST_TITLE = True

def printr(msg, color, atrs=None):
	if atrs is None:
		atrs = []

	if USE_COLOR:
		cprint(msg, color, attrs=atrs)
	else:
		clprint(msg, color, attrs=atrs)

def set_dir(d):
	global PDIR
	PDIR = d.replace(USR_PATH, "~")

def print_event(event, *args):
	global FIRST_TITLE
	global PDIR

	l = loc[event]
	atrs = []

	if event in ["overwrite", "add"]:
		printr(l.format(shrt(args[0]), shrt(args[1])), "cyan", atrs)
	elif event in ["unzip", "untar", "embed", "full_lib"]:
		printr(l.format(shrt(args[0]), shrt(args[1])), "magenta", atrs)
	elif event in ["wget", "clone"]:
		printr(l.format(shrt(args[0]), shrt(args[1])), "yellow", atrs)
	elif event in ["parts", "created"]:
		printr(l.format(shrt(args[0])), "cyan", atrs)
	elif event == "ignored":
		printr(l.format(shrt(args[0])), "magenta", atrs)
	elif event == "removed":
		printr(l.format(shrt(args[0])), "red", atrs)
	elif event == "compiling":
		printr(l.format(shrt(args[0])), "white", atrs)
	elif event == "symlink":
		printr(l.format(shrt(args[0]), shrt(args[1])), "cyan", atrs)
	elif event == "import":
		p = args[0]
		printr(l.format(shrt(p["name"]), p["version"]), "magenta", atrs)
	else:
		l = l[args[0]]
		if event == "action":
			if not FIRST_TITLE:
				print ""

			if args[0] not in ["selfupdate", "upgrade", "import"]:
				if PDIR is None:
					PDIR = dirname(shrt(args[1]))
				l = l.format(shrt(args[1]))

			FIRST_TITLE = False
			printr(l, "white", ["bold", "underline"] + atrs)
		elif event == "notice":
			printr(l[args[1]], "green", atrs)
		elif event == "embed":
			printr(l, "green", atrs)
		elif event == "success":
			if args[0] in ["upgrade", "import", "build"]:
				printr(l, "green", atrs)
			elif args[0] in ["compiling"]:
				printr(l.format(shrt(args[1])), "green", atrs)
			else:
				sa = args[1]
				printr(l.format(sa), "green", atrs)
		elif event == "warning":
			printr(l.format(args[1]), "yellow", atrs)
		elif event == "alert":
			printr(l, "red", atrs)
		elif event == "exception":
			k = args[0]
			if k in ["invalid_file", "missing_tag", "missing_resource"]:
				printr(l.format(args[1], args[2]), "red", atrs)
			elif k == "missing_property":
				printr(l.format(args[1], pformat([2])), "red", atrs)
			else:
				sa = args[1]
				printr(l.format(sa), "red", atrs)
		else:
			cprint(event, "green")
			print event, ": [{0}]".format(",".join(args))

