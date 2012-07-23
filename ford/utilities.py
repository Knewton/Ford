#!/usr/bin/env python
from os.path import expanduser, isdir, exists, join, abspath
from os import mkdir, makedirs, listdir
from errno import EEXIST
from subprocess import Popen, PIPE, STDOUT
from types import ListType
from shutil import copyfile

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

def call(command, exit_on_failure=False):
	if type(command) == ListType:
		command = " ".join(command)
	process = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
	print process.communicate()[0]
	code = process.returncode
	if exit_on_failure:
		if code != 0:
			exit(1)
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
			dest_fp = ".{0}".format(f[1:])
		else:
			dest_fp = join(dest, f)

		if isdir(fp):
			if copy_missing_files(fp, join(dest, f), force, underscore):
				had_file = True
		else:
			if exists(dest_fp) and not force:
				continue
			print "Adding {0}".format(dest_fp)
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
