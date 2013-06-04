#!/usr/bin/env python
# Copyright (c) 2013 Knewton
#
# Dual licensed under:
#   MIT: http://www.opensource.org/licenses/mit-license.php
#   GPLv3: http://www.opensource.org/licenses/gpl-3.0.html

"""Ford is a web application development and compilation tool."""

#------------------------------
#
# Includes
#
#------------------------------

#------------------------------
# Built-in
#------------------------------

from json import dumps, loads
from os import makedirs, remove, symlink, getcwd, listdir, chdir
from os.path import (realpath, exists, isfile, isdir, join, expanduser,
	dirname, basename, splitext, split, normpath)
from re import findall, sub
from shutil import copyfile, copytree, rmtree
from sys import exit
from time import time
from urllib2 import urlopen, HTTPError
from subprocess import call as subcall

#------------------------------
# Third-party
#------------------------------

from BeautifulSoup import BeautifulSoup, Tag

#------------------------------
# Project
#------------------------------

from utilities import (mkdirp, read_file, write_file, call, merge_directories,
	fix_path, unpackage, loc, printr, set_dir)
from utilities import print_event as pe

#------------------------------
#
# Module info
#
#------------------------------

__author__= "Eric Garside"
__copyright__ = "Copyright (c) 2013 Knewton"
__version__ = "1.0.0"
__license__ = "GPLv3, MIT"
__maintainer__ = "Eric Garside"
__email__ = "eric@knewton.com"
__status__ = "Development"

#------------------------------
#
# Constants
#
#------------------------------

#------------------------------
# System paths
#------------------------------

BUILD_TARGET = "{0}/build_targets/{1}.json"
USER_DIR = expanduser("~/.ford")
SCRIPT_DIR = join(USER_DIR, "scripts")

#------------------------------
# Web Installer
#------------------------------

WI_LOG = "/tmp/Ford.web_install.latest"
SUP_CMD = "curl {0} | WI_CONFIRM=true sh"
WEB_INSTALLER = "https://raw.github.com/Knewton/Ford/master/web_install.sh"

#------------------------------
# Import: Standard
#------------------------------

EXT_MANIFESTS = "https://github.com/Knewton/Ford-Manifests/archive/master.zip"
EXT_MANIFEST_DIR = "Ford-Manifests-master"

EXT_TEMPLATES = "https://github.com/Knewton/Ford-Templates/archive/master.zip"
EXT_TEMPLATE_DIR = "Ford-Templates-master"

#------------------------------
# Import: CDNJS
#------------------------------

CDNJS_URL = "http://cdnjs.cloudflare.com/ajax/libs/{0}/{1}/{2}"
CDNJS_CACHE = join(USER_DIR, "cdnjs.com.packages.json")
CDNJS_REPO = "http://cdnjs.com/packages.json"

#------------------------------
# Cert file
#------------------------------

CERT_FILE = join(USER_DIR, "localhost.pem")

#------------------------------
# Upgrade
#------------------------------

SRC_DIR = dirname(__file__)
TARGETS = ["scripts"]

#------------------------------
# Init
#------------------------------

DEFAULT_TEMPLATE = "web-application"
PROJECT_DIRS = ["lib", "manifests"]

#------------------------------
# Single file
#------------------------------

JSPACK = "window.fordPacked=true;window.fordSrc={};"
JS = "window.fordSrc['{0}']="

#------------------------------
# Update and Build
#------------------------------

VALID_COMPS = ["html", "css", "js", "images"]
VALID_MIME = {
	"js": ["text/plain", "application/x-javascript", "text/javascript",
		"application/javascript"],
	"json": ["application/json"],
	"css": ["text/plain", "text/css"],
	"html": ["text/plain", "text/html"],
	"zip": ["application/zip"],
	"images": ["image/png"]
}

#------------------------------
# Excptions
#------------------------------

class UpdateError(Exception):
	pass

#------------------------------
# Custom tags
#------------------------------

# Add tags to beautifulsoup or HTML will not build properly
CUSTOM_TAGS = ("group", "component", "def", "sect")
BeautifulSoup.NESTABLE_BLOCK_TAGS += CUSTOM_TAGS
for t in CUSTOM_TAGS:
	BeautifulSoup.NESTABLE_TAGS[t] = []

#------------------------------
#
# Utilities
#
#------------------------------

#------------------------------
# Generic
#------------------------------

def expand_namespace(shorthand, obj):
	for i in shorthand[1]:
		obj[shorthand[0] + i] = "."

def replace_library(library, project):
	if "use_as" in project.manifest:
		if library in project.manifest["use_as"]:
			return project.manifest["use_as"][library]
	return library

def expand_libs(libs, project):
	if not hasattr(libs, "keys"):
		b = {}
		for l in libs:
			if isinstance(l, basestring):
				l = replace_library(l, project)
				b[l] = "."
			else:
				expand_namespace(l, b)
		libs = b

	if "&" in libs:
		for l in libs["&"]:
			if isinstance(l, basestring):
				l = replace_library(l, project)
				libs[l] = "."
			else:
				expand_namespace(l, libs)
		del libs["&"]

	return libs

def expand_manifest(lib, m, project):
	new_manifest = {}
	lib_resources = []

	for k in m:
		v = m[k]
		if "reqs" in v:
			v["reqs"] = expand_libs(v["reqs"], project)

		if k[:1] == "@":
			if "resources" in v:
				resources = v["resources"]
				gk = k[1:]
				if lib not in project.libGroups:
					project.libGroups[lib] = {}
				project.libGroups[lib][gk] = resources
				del v["resources"]
				lib_resources += resources

				for rsc in resources:
					new_manifest[rsc] = v

				continue
		elif k != "application":
			lib_resources.append(k)

		new_manifest[k] = v

	if "application" in new_manifest:
		new_manifest["application"]["reqs"]["."] = lib_resources

	return new_manifest


def get_json(fp):
	if not exists(fp):
		pe("exception", "missing_file", fp)
		exit(1)
	try:
		return loads(read_file(fp))
	except ValueError:
		pe("exception", "invalid_file", "json", fp)
		exit(1)

def get_manifest(lib):
	return get_json("{0}/manifest.json".format(lib))

def split_uri(uri):
	# use git for blah.com/foo.git
	if uri[-4:] == ".git":
		protocol = "git"
	# :// is some protocol
	elif "://" in uri:
		return uri.split("://")
	# // means http
	elif uri[0:2] == "//":
		protocol = "http"
		uri = uri[2:]
	# use git for blah.com:/foo|blah.com:foo but not foo.com:80/blah
	elif ":" in uri:
		url, path = uri.split(":")
		parts = path.split("/")
		port = parts.pop(0)
		fp = "/".join(parts)
		if not port.isdigit():
			protocol = "git"
	# everything else should be file
	else:
		protocol = "file"
		# Handle ~ in the path
		uri = realpath(expanduser(uri))
	return protocol, uri

def mime_valid(expected, ftype):
	for mime in VALID_MIME[ftype]:
		if mime in expected:
			return True
	return False

def wget(url, ftype, dest):
	try:
		pe("wget", url, dest)
		resp = urlopen(url)
		headers = resp.headers
		if not mime_valid(headers["content-type"], ftype):
			raise UpdateError(loc["exception"]["invalid_mime"].format(url,
					", ".join(VALID_MIME[ftype])))
		write_file(dest, resp.read())
	except HTTPError as e:
		raise UpdateError(loc["exception"]["http"].format(str(e), url))
		exit(1)

# Author: Cimarron Taylor
# Date: July 6, 2003
# File Name: relpath.py
# Program Description: Print relative path from /a/b/c/d to /a/b/c1/d1

def pathsplit(p, rest=[]):
	(h,t) = split(p)
	if len(h) < 1: return [t]+rest
	if len(t) < 1: return [h]+rest
	return pathsplit(h,[t]+rest)

def commonpath(l1, l2, common=[]):
	if len(l1) < 1: return (common, l1, l2)
	if len(l2) < 1: return (common, l1, l2)
	if l1[0] != l2[0]: return (common, l1, l2)
	return commonpath(l1[1:], l2[1:], common+[l1[0]])

def relpath(p1, p2):
	(common,l1,l2) = commonpath(pathsplit(p1), pathsplit(p2))
	p = []
	if len(l1) > 0:
		p = [ '../' * (len(l1) - 1) ] # Was adding one too many for pathing
	p = p + l2
	return join( *p )

def relative_symlink(uri, dest):
	cur = getcwd()
	d = dirname(dest)
	n = basename(dest)
	r = relpath(dest, uri)

	pe("symlink", uri, dest, r, n)

	chdir(d)
	symlink(r, n)
	chdir(cur)

#------------------------------
# Self update
#------------------------------

def selfupdate():
	pe("action", "selfupdate")
	pe("alert", "sudo")
	call("sudo touch /tmp/ford_sudo.permission")
	if call(SUP_CMD.format(WEB_INSTALLER), tab=True) == 0:
		pe("success", "selfupdate", WI_LOG)
	else:
		pe("exception", "selfupdate", WI_LOG)
		exit(1)

#------------------------------
# Cert for SSL
#------------------------------

def makecert():
	print "\n" * 3
	print "!" * 65
	print "! You can leave everything blank EXCEPT the FQDN of your server !"
	print "! This is the 'Common Name' field during certificate generation !"
	print "! You should make this whatever name you plan on accessing your !"
	print "! server from (Ex: localhost)                                   !"
	print "!" * 65
	print "\n" * 3

	if isfile(CERT_FILE):
		remove(CERT_FILE)

	if not isfile(CERT_FILE):
		subcall(["openssl", "req", "-new", "-x509", "-keyout", CERT_FILE,
			"-out", CERT_FILE, "-days", "365", "-nodes"])

#------------------------------
# CDNJS import
#------------------------------

def cdnimport(force):
	pe("action", "import")
	if force and isfile(CDNJS_CACHE):
		remove(CDNJS_CACHE)

	if not isfile(CDNJS_CACHE):
		wget(CDNJS_REPO, "json", CDNJS_CACHE)

	packages = get_json(CDNJS_CACHE)
	upgraded = False

	for p in packages["packages"]:
		if not "name" in p:
			continue

		resource_path = join(USER_DIR, "manifests",
				"{0}.json".format(p["name"]))

		if isfile(resource_path):
			m = get_json(resource_path)
			rsc = m[p["name"]]

			# Only overwrite autogenerated manifests
			if "autogenerated" not in rsc or not rsc["autogenerated"]:
				continue

			if "version" in rsc and "version" in p:
				if p["version"] == rsc["version"] and not force:
					continue

		upgraded = True
		pe("import", p)
		manifest = {}
		manifest[p["name"]] = {
			"version": p["version"],
			"autogenerated": True,
			"comp": ["js"],
			"uri": CDNJS_URL.format(p["name"], p["version"], p["filename"])
		}
		write_file(resource_path, dumps(manifest))

	if not upgraded:
		pe("notice", "import", "nothing")
	else:
		pe("success", "import")

#------------------------------
# HTML
#------------------------------

def replace_element(element, replacement=None):
	if replacement is not None:
		element.replaceWith(replacement)
	else:
		element.extract()

def merge_classes(element, target):
	if not "class" in element:
		return

	classes = element["class"].split()

	if not "class" in target:
		tClasses = []
	else:
		tClasses = target["class"].split()

	add = []
	for cName in classes:
		if cName == "component":
			continue
		if not cName in tClasses:
			add.append(cName)
	if len(add):
		target["class"] = " ".join(add)

def merge_sections(element, target):
	smap = {}
	sections = element.findAll("def")
	tSections = target.findAll("sect")

	for section in sections:
		smap[section["class"]] = section.renderContents()

	for tSection in tSections:
		replacement = None
		if tSection["class"] in smap:
			replacement = smap[tSection["class"]]
		replace_element(tSection, replacement)

def lib_path(lib):
	return "lib/{0}".format(lib)

#------------------------------
#
# Upgrade
#
#------------------------------

def get_external(force=False):
	dest = fix_path("/tmp/ford_manifests.zip")
	wget(EXT_MANIFESTS, "zip", dest)
	manifests = unpackage(dest)
	src = "/tmp/ford_manifests/{0}".format(EXT_MANIFEST_DIR)
	ret = merge_directories(src, "~/.ford/manifests", None, force)

	pe("removed", dest)
	remove(dest)
	pe("removed", manifests)
	rmtree(manifests)

	dest = fix_path("/tmp/ford_templates.zip")
	wget(EXT_TEMPLATES, "zip", dest)
	templates = unpackage(dest)
	src = "/tmp/ford_templates/{0}".format(EXT_TEMPLATE_DIR)
	ret = merge_directories(src, "~/.ford/templates", None, force)

	pe("removed", dest)
	remove(dest)
	pe("removed", templates)
	rmtree(templates)

	return ret

def upgrade(force=False):
	pe("action", "upgrade")
	upgraded = False

	# Python can only reliably copy one level deep with setup tools, afaict.
	# Only using it for scripts now.
	if merge_directories(SRC_DIR, "~/.ford", TARGETS, force):
		upgraded = True

	if get_external(force):
		upgraded = True

	if not upgraded:
		pe("notice", "upgrade", "nothing")
	else:
		pe("success", "upgrade")

#------------------------------
#
# Project
#
#------------------------------

class Project(object):

	#------------------------------
	#
	# Constructor
	#
	#------------------------------

	def __init__(self, project_dir, project_manifest):
		# Define properties
		self.project_dir = realpath(project_dir)
		self.project_manifest = realpath(project_manifest)
		self.output_dir = None
		self.libraries = {}
		self.libGroups = {}
		self.included = {}
		self.unpacked = {}
		self.held_resources = {}
		self.tmp_paths = {}
		self.pending_resources = 0
		self.content = None
		self.manifest = None
		self.build_project = False
		self.single_file = False
		self.rawsrc = False
		self.update_project = True
		self.cut_outs = []

		# For output formatting
		set_dir(self.project_dir)

	#------------------------------
	#
	# Internal methods
	#
	#------------------------------

	#------------------------------
	# Builder utilities
	#------------------------------

	def _prepare(self):
		self.content = {"html": {}, "css": [], "js": []}
		self.libraries = {}
		self.libGroups = {}
		self.included = {}
		self.unpacked = {}
		self.held_resources = {}
		self.tmp_paths = {}
		self.pending_resources = 0
		self.cut_outs = []

		if "cut_out" in self.manifest:
			for lib in self.manifest["cut_out"]:
				rscs = self.manifest["cut_out"][lib]
				for rsc in rscs:
					for comp in rscs[rsc]:
						s = "lib/{0}/{1}/{1}.{2}".format(lib, rsc, comp)
						self.cut_outs.append(s)

	def _manifest_flag(self, name):
		if not name in self.manifest:
			return False
		return self.manifest[name]

	def _compile(self, ftype, name):
		cmd = ["juicer", "merge", "--force", "--document-root",
				"'{0}'".format(self.project_dir)]
		src_file = "{0}/{2}.{1}".format(self.output_dir, ftype, name)
		out_file = "{0}/{2}.min.{1}".format(self.output_dir, ftype, name)
		if ftype == "js":
			cmd += ["--skip-verification"]
			if self._manifest_flag("rawsrc") or self.rawsrc:
				cmd += ['--minifyer ""']
		elif ftype == "css":
			cmd += ["--force-image-embed", "--embed-images", "data_uri"]
		cmd += ["'{0}'".format(src_file)]
		if call(cmd) == 0:
			if self._manifest_flag("rawsrc") or self.rawsrc:
				pe("warning", "compiling", src_file)
				copyfile(out_file, src_file)
				remove(out_file)
			else:
				pe("success", "compiling", src_file)
				remove(src_file)
		else:
			pe("exception", "compiling", src_file)
			exit(1)

	def _expand_component_group(self, component):
		cid = component["id"]
		parts = cid.split("@")
		lib = parts.pop(0)
		group = "-".join(parts)

		if not lib in self.libGroups:
			pe("exception", "missing_property", lib, self.libGroups)
			exit(1)

		groups = self.libGroups[lib]

		if not group in groups:
			pe("exception", "missing_property", group, group)
			exit(1)

		resources = groups[group]
		index_idx = component.parent.contents.index(component)
		for resource in resources:
			tpl = '<component id="{0}-{1}"></component>'.format(lib, resource)
			component.parent.insert(index_idx + 1, BeautifulSoup(tpl))

		replace_element(component)

	def _insert_component(self, component):
		cid = component["id"]
		parts = cid.split("-")
		lib = parts.pop(0)
		resource = "-".join(parts)
		html = self.content["html"]
		if not lib in html:
			pe("exception", "missing_property", "html", lib)
			exit(1)
		if not resource in html[lib]:
			pe("exception", "missing_property", resource, html[lib].keys())
			exit(1)

		element = BeautifulSoup(html[lib][resource])
		merge_classes(component, element)
		merge_sections(component, element)
		replace_element(component, element)

	def _resolve_component_html(self, doc):
		groups = doc.findAll("group")
		for g in groups:
			self._expand_component_group(g)
		doc = BeautifulSoup(str(doc))

		components = doc.findAll("component")
		for c in components:
			self._insert_component(c)
		doc = BeautifulSoup(str(doc))
		if len(doc.findAll("component")) > 0 or len(doc.findAll("group")) > 0:
			doc = self._resolve_component_html(doc)
		return doc

	def _complete(self):
		pe("action", "build", self.current_manifest)

		js_path, css_path, html_path = [None] * 3
		jsn, csn = ["application"] * 2
		htn = "index"
		if "output" in self.manifest:
			op = self.manifest["output"]
			path = "{0}/application".format(self.output_dir)
			if not (isinstance(op, basestring) or isinstance(op, str)):
				if "js" in op:
					jsn = op["js"]

				if "css" in op:
					csn = op["css"]

				if "html" in op:
					htn = op["html"]

				js_path = "{0}/{1}".format(self.output_dir, jsn)
				css_path = "{0}/{1}".format(self.output_dir, csn)
				html_path = "{0}/{1}".format(self.output_dir, htn)
		else:
			path = "{0}/application".format(self.output_dir)

		has_css, has_js = False, False
		if css_path is not None:
			path = css_path
		if len(self.content["css"]):
			css = []
			fp = "{0}.css".format(path)
			pe("compiling", fp)
			for p in self.content["css"]:
				part = "{0}/{1}".format(self.project_dir, p)
				if p not in self.cut_outs:
					pe("parts", part)
					css.append("@import url(/{1})".format(self.project_dir, p))
				else:
					pe("ignored", part)
			write_file(fp, "\n".join(css) + "\n")
			self._compile("css", csn)
			has_css = True

		if js_path is not None:
			path = js_path
		if len(self.content["js"]):
			js = []
			fp = "{0}.js".format(path)
			pe("compiling", fp)
			for p in self.content["js"]:
				part = "{0}/{1}".format(self.project_dir, p)
				if p not in self.cut_outs:
					pe("parts", part)
					js.append(" * @depends /{1}".format(self.project_dir, p))
				else:
					pe("ignored", part)
			content = "/**\n{0}\n */\n".format("\n".join(js))
			write_file(fp, content)
			self._compile("js", jsn)
			has_js = True

		if html_path is not None:
			path = html_path

		build_index = True
		if "library" in self.manifest:
			build_index = not self.manifest["library"]

		dirs_to_copy = []
		if "directories" in self.manifest:
			dirs_to_copy = self.manifest["directories"]
		if build_index:
			dirs_to_copy.append("localization")

		for d in dirs_to_copy:
			location = "{{0}}/{0}".format(d)
			if exists(location.format(self.project_dir)):
				if exists(location.format(self.output_dir)):
					rmtree(location.format(self.output_dir))
				copytree(location.format(self.project_dir),
							location.format(self.output_dir))

		if build_index:
			index = "{{0}}/{0}.html".format(htn)
			src = index.format(self.project_dir)
			if not exists(src):
				pe("exception", "missing_file", src)
				exit(1)
			index_html = BeautifulSoup(read_file(src))

			bootstrap = index_html.findAll(id="bootstrap")
			if len(bootstrap) == 0:
				pe("exception", "missing_tag", "bootstrap",
						"{0}.html".format(htn))
				exit(1)
			bootstrap = bootstrap[0]
			index_idx = bootstrap.parent.contents.index(bootstrap)

			use_single = self._manifest_flag("embed") or self.single_file
			rp = []

			index_page = index.format(self.output_dir)
			cb = str(time())

			if has_js:
				script = Tag(index_html, "script")
				script["type"] = "text/javascript"
				if use_single:
					script.append("$FRD" + str(len(rp)))
					d = "{0}.min.js".format(path)
					rp.append(read_file(d))
					pe("embed", d, index_page)
				elif self._manifest_flag("rawsrc") or self.rawsrc:
					script["src"] = "{1}.js?_={0}".format(cb, jsn)
				else:
					script["src"] = "{1}.min.js?_={0}".format(cb, jsn)
				bootstrap.parent.insert(index_idx + 1, script)

			# Package the scripts first, cause we prepend the js def later
			if use_single and "package_scripts" in self.manifest:
				bootstrap.parent.insert(index_idx + 1, script)
				for f in self.manifest["package_scripts"]:
					fpath = join(self.output_dir, f)
					if isfile(fpath):
						script = Tag(index_html, "script")
						script["type"] = "text/javascript"
						script.append(JS.format(f) +
							"$FRD" + str(len(rp)) + ";")
						bootstrap.parent.insert(index_idx + 1, script)
						rp.append(read_file(fpath))
						pe("embed", fpath, index_page)

				# Insert preface tag with defs to prepare the package.
				script = Tag(index_html, "script")
				script["type"] = "text/javascript"
				script.append(JSPACK)
				bootstrap.parent.insert(index_idx + 1, script)

			if has_css:
				if use_single:
					d = "{0}.min.css".format(path)
					style = Tag(index_html, "style")
					style["media"] = "screen, print"
					style["type"] = "text/css"
					style.string = read_file(d)
					pe("embed", d, index_page)
				else:
					style = Tag(index_html, "link")
					style["media"] = "screen, print"
					style["rel"] = "stylesheet"
					style["type"] = "text/css"
					if self._manifest_flag("rawsrc") or self.rawsrc:
						style["href"] = "{1}.css?_={0}".format(cb, csn)
					else:
						style["href"] = "{1}.min.css?_={0}".format(cb, csn)
				bootstrap.parent.insert(index_idx + 1, style)

			# Remove the bootstrap tag
			bootstrap.extract()

			# Handle component HTML
			index_html = self._resolve_component_html(index_html)
			write_file(index.format(self.output_dir), str(index_html))
			pe("success", "application", index_page)

			# Beautifulsoup doesn't do well with this
			if len(rp):
				fdata = read_file(index.format(self.output_dir))
				idx = 0
				for repl in rp:
					fdata = fdata.replace("$FRD" + str(idx), repl)
					idx += 1
				write_file(index.format(self.output_dir), fdata)
		else:
			pe("success", "lib", self.current_manifest)

	#------------------------------
	# Dependency management
	#------------------------------

	def _make_tmp(self, uri=None, rsc=None, rm=False):
		fp = join(self.project_dir, "tmp")
		if rm:
			if exists(fp):
				pe("removed", fp)
				rmtree(fp)
		elif not exists(fp):
			pe("created", fp)
			mkdirp(fp)

		if uri is not None:
			if uri in self.tmp_paths:
				repo = self.tmp_paths[uri]
			else:
				repo = join(fp, rsc)
				self.tmp_paths[uri] = repo
			fp = repo

		return fp

	def _clean_tmp(self):
		self._make_tmp(rm=True)

	def _load_application_resources(self):
		if self.build_project:
			if "application" in self.manifest:
				app = self.manifest["application"]
				if "scripts" in app and len(app["scripts"]) > 0:
					for s in app["scripts"]:
						self.content["js"].append("{0}.js".format(s))
				if "styles" in app and len(app["styles"]) > 0:
					for s in app["styles"]:
						self.content["css"].append("{0}.css".format(s))
			self._complete()
		self._clean_tmp()
		pe("success", "build")

	def _has_library_resource(self, lib, resource):
		if not lib in self.included:
			self.included[lib] = {}

		if not resource in self.included[lib]:
			return False
		else:
			return self.included[lib][resource]["included"]

	def _missing_reqs(self, reqs, pending_lib, pending_resource):
		missing = {}

		for lib in reqs:
			req_resources = reqs[lib]

			# In reqs, a 'dot' as a project name means 'use my project'
			if lib == ".":
				lib = pending_lib

			if not lib in self.held_resources:
				self.held_resources[lib] = {}

			if req_resources in [".", "*"]:
				req_resources = [lib]
			for resource in req_resources:
				if not self._has_library_resource(lib, resource):
					if not resource in self.held_resources[lib]:
						self.held_resources[lib][resource] = {}
					held = self.held_resources[lib]
					if not pending_lib in held[resource]:
						held[resource][pending_lib] = []
					held[resource][pending_lib].append(pending_resource)
					if not lib in missing:
						missing[lib] = []
					missing[lib].append(resource)

		return missing

	def _remove_hold(self, held, lib, resource):
		for library in held:
			for held_resource in held[library]:
				pending_lib = self.included[library]
				if not held_resource in pending_lib:
					return
				pending_lib = pending_lib[held_resource]
				for held_lib in pending_lib["requires"]:
					if held_lib == lib:
						pending_resources = pending_lib["requires"][held_lib]
						for pending_resource in pending_resources:
							if pending_resource == resource:
								idx = pending_resources.index(pending_resource)
								del pending_resources[idx]

	def _resource_included(self, lib, resource):
		status = self.included[lib][resource]
		status["loading"] = False
		status["included"] = True
		if lib in self.held_resources:
			held_resources = self.held_resources[lib]
			if resource in held_resources:
				self._remove_hold(held_resources[resource], lib, resource)
				self._load_resources(held_resources[resource])
		self.pending_resources -= 1

	def _include(self, lib, resource, comp):
		if self.build_project:
			path = "{0}/{1}/{1}".format(lib_path(lib), resource)
			for ftype in comp:
				if ftype == "js":
					self.content["js"].append("{0}.js".format(path))
				elif ftype == "css":
					self.content["css"].append("{0}.css".format(path))
				elif ftype == "html":
					if not lib in self.content["html"]:
						self.content["html"][lib] = {}
					h = "{0}.html".format(path)
					self.content["html"][lib][resource] = read_file(h)
		self._resource_included(lib, resource)

	def _track_resource(self, lib, resource, details):
		if "reqs" in details:
			missing = self._missing_reqs(details["reqs"], lib, resource)
		else:
			missing = {}

		return {
			"included": False,
			"loading": False,
			"requires": missing
		}

	def _get(self, lib, resource, protocol, uri, ftype, fp=None, img=None,
			link=False):
		path = lib_path(lib)
		resource_path = join(self.project_dir, path, resource)

		if fp is not None:
			# Append resource name if the pointer ends with a slash
			if fp[-1] == "/":
				fp += resource
			fprotocol, fpuri = split_uri(fp)
			if fprotocol in ["http", "https"]:
				protocol = fprotocol
				uri = fpuri
				fp = None

		if protocol == "git":
			repo = self.tmp_paths[uri]
			protocol = "file"
			if fp is None:
				uri = repo
			else:
				uri = join(repo, fp)
			fp = None

		if fp is not None:
			uri = "/".join([uri, fp])
		if ftype != "images":
			uroot, uext = splitext(uri)
			expect = ".{0}".format(ftype)
			if uext != expect:
				uri += expect

		if ftype == "images":
			resource_path += "/images"
			if img is not None:
				fname = img
			else:
				fname = basename(uri)
			froot, fext = splitext(fname)
			if fext == "":
				root, ext = splitext(uri)
				fname = "".join([fname, ext])
		else:
			fname = ".".join([resource, ftype])

		mkdirp(resource_path)
		err = loc["exception"]["resource"].format(lib, resource) + ":\n"

		dest = join(resource_path, fname)
		if protocol in ["http", "https"]:
			url = "://".join([protocol, uri])
			wget(url, ftype, dest)
		elif protocol == "file":
			if not isfile(uri):
				raise UpdateError(err +
						loc["exception"]["missing_file"].format(uri))
				exit(1)
			mkdirp(dirname(dest))
			try:
				if link:
					try:
						remove(dest)
						pe("removed", dest)
					except OSError:
						pass
					relative_symlink(uri, dest)
				else:
					pe("add", uri, dest)
					copyfile(uri, dest)
			except IOError as e:
				raise UpdateError(err +
						loc["exception"]["copying"].format(uri, str(e)))
		return dest

	def _update_resource(self, lib, resource, details, base=None):
		uri = None
		if base is not None:
			details.update(base)

		if "link" in details:
			l = details["link"]
		else:
			l = False

		for f in ["uri", "url", "path"]:
			if f in details:
				uri = details[f]
				del details[f]
				break

		lib_target = None
		append_name = False
		if uri is None:
			protocol, uri = "http", ""
		else:
			protocol, uri = split_uri(uri)
			# If the string ends with a slash, assume we should add the name
			if uri[-1] == "/":
				append_name = True
				uri = uri[:-1]

		full_library = False
		if resource == ".":
			full_library = True
			resource = lib

		if protocol == "git":
			repo = self._make_tmp(uri, lib)
			lib_target = repo
			if not isdir(repo):
				pe("clone", uri, repo)
				call(["git", "clone", "'{0}' '{1}'".format(uri, repo)])
			if "root" in details and uri + "_orig" not in self.tmp_paths:
				self.tmp_paths[uri + "_orig"] = repo
				repo = join(repo, details["root"])
				self.tmp_paths[uri] = repo

		if protocol in ["http", "https"] and "packaged" in details:
			url = "://".join([protocol, uri])
			protocol = "file"
			dest = self._make_tmp(uri, lib) + "." + details["packaged"]
			if not dest in self.unpacked:
				wget(url, details["packaged"], dest)
				self.unpacked[dest] = unpackage(dest)
			uri = self.unpacked[dest]
			append_name = True
			if "root" in details:
				uri = join(uri, details["root"])
			lib_target = uri

		if full_library:
			if lib_target is None:
				raise UpdateError(loc["exception"]["missing_lib"].format(lib))
			full_lib_path = lib_path(lib)
			full_lib_dest = join(self.project_dir, full_lib_path)
			if isdir(full_lib_dest):
				rmtree(full_lib_dest)
			pe("full_lib", lib_target, full_lib_dest)
			copytree(lib_target, full_lib_dest)
			gitdir = join(full_lib_dest, ".git")
			if isdir(gitdir):
				rmtree(gitdir)
			return

		if not "comp" in details:
			pe("exception", "missing_property", "comp", details)
			exit(1)

		comp = details["comp"]

		def handle_images(imgs=None):
			if protocol == "git":
				path = repo
				iprotocol = "file"
			else:
				path = uri
				iprotocol = protocol
			if not append_name:
				path = path[:path.rfind("/")]
			i = "images"
			if ftype == "images/" or imgs is None:
				if isinstance(imgs, basestring) or isinstance(imgs, str):
					path = "{0}/{1}".format(path, imgs)
					imgs = None
				else:
					path = "{0}/images".format(path)
				if imgs is None:
					imgs = listdir(path)

			if hasattr(imgs, "keys"):
				for name in imgs.keys():
					img = imgs[name]
					self._get(lib, resource, iprotocol, path, i, img, name, l)
			else:
				for img in imgs:
					self._get(lib, resource, iprotocol, path, i, img, None, l)

		comp_err = loc["exception"]["bad_comp"].format(lib, resource)

		def cleanup(df, ft, dt):
			# Cleans up destination files
			if ft == "css":
				fc = read_file(df)
				if "cssImageFix" in dt:
					fix = dt["cssImageFix"]
					if isinstance(fix, basestring) or isinstance(fix, str):
						fix = [fix]
					for fx in fix:
						fc = fc.replace(fx, "images")
				for m in findall('url\(([^)]+)\)', fc):
					u = m.replace("'", "").replace('"', "")
					if "images/" not in u:
						u = "images/{0}".format(u)
					fc = fc.replace(m, u)
				# Strip strings from images
				write_file(df, fc)

		if protocol == "git":
			append_name = True
		if hasattr(comp, "keys"):
			comps = []
			for ftype in comp.keys():
				if not ftype in VALID_COMPS and ftype != "images/":
					raise UpdateError(comp_err.format(ftype))
				if ftype in ["images", "images/"]:
					comps.append("images")
					handle_images(comp[ftype])
				else:
					comps.append(ftype)
					df = self._get(lib, resource, protocol, uri, ftype,
							comp[ftype], None, l)
					cleanup(df, ftype, details)
			details["comp"] = comps
		else:
			for ftype in comp:
				if not ftype in VALID_COMPS and ftype != "images/":
					raise UpdateError(comp_err.format(ftype))
				if ftype in ["images", "images/"]:
					if not "images" in details:
						details["images"] = None
					handle_images(details["images"])
					del details["images"]
				else:
					fp = None
					if append_name:
						fp = "{0}.{1}".format(resource, ftype)
					df = self._get(lib, resource, protocol, uri, ftype, fp,
							None, l)
					cleanup(df, ftype, details)
			details["comp"] = [x if x != "images/" else "images" for x in comp]

	def _update_library(self, lib):
		manifest_path = "{0}/manifests/{1}.json".format(self.project_dir, lib)
		if not exists(manifest_path):
			manifest_path = "{0}/manifests/{1}.json".format(USER_DIR, lib)
		try:
			manifest = get_json(manifest_path)
		except:
			return

		write_manifest = True
		try:
			base = None
			if "*" in manifest:
				base = manifest["*"]
				del manifest["*"]
			if "." in manifest:
				write_manifest = False
			if "skip_update" in self.manifest:
				if lib not in self.manifest["skip_update"]:
					for resource in manifest:
						details = manifest[resource]
						self._update_resource(lib, resource, details, base)
		except UpdateError as e:
			printr(e, "red")
			exit(1)

		lib_manifest = join(self.project_dir, lib_path(lib), "manifest.json")
		if write_manifest:
			write_file(lib_manifest, dumps(manifest))
		return lib_manifest

	def _include_library_resource(self, lib, resource):
		manifest = self.libraries[lib]
		includes = self.included[lib]

		if not resource in manifest:
			pe("exception", "missing_resource", resource, lib)
			exit(1)

		details = manifest[resource]

		if not resource in includes:
			includes[resource] = self._track_resource(lib, resource, details)
			self.pending_resources += 1

		status = includes[resource]

		if not status["included"]:
			has_requirements = False
			if len(status["requires"]) > 0:
				for req_lib in status["requires"]:
					if len(status["requires"][req_lib]) > 0:
						has_requirements = True
						break;

			if has_requirements:
				self._load_resources(status["requires"])
			elif not status["loading"]:
				status["loading"] = True
				self._include(lib, resource, details["comp"])

	def _include_library_resources(self, lib, resources):
		if not lib in self.libraries:
			if self.update_project:
				self._update_library(lib)
			path = lib_path(lib)
			self.libraries[lib] = expand_manifest(lib,
				get_manifest(lib_path(lib)), self)
			self.included[lib] = {}

		replaced = lib
		lib = replace_library(lib, self)
		if lib == replaced:
			replaced = None

		if resources in [".", "*"]:
			resources = [lib]
		for r in resources:
			if r == replaced:
				r = lib
			self._include_library_resource(lib, r)

	def _load_resources(self, includes, proceed_if_empty=False):
		has_resources = False

		includes = expand_libs(includes, self)

		for lib in includes:
			has_resources = True
			self._include_library_resources(lib, includes[lib])

		if not has_resources and proceed_if_empty:
			self._load_application_resources()

	def _handle_project_dependencies(self):
		if "includes" in self.manifest:
			self._load_resources(self.manifest["includes"], self.build_project)
		if self.pending_resources == 0:
			self._load_application_resources()

	#------------------------------
	#
	# External methods
	#
	#------------------------------

	#------------------------------
	# Init
	#------------------------------

	def init(self, template=None, force=False, explicit=False):
		cur_template = join(self.project_dir, ".template")
		if template is None:
			if isfile(cur_template):
				template = read_file(cur_template)
			else:
				template = DEFAULT_TEMPLATE
				if not explicit:
					pe("exception", "not_project", self.project_dir)
					return False

		pe("action", "init", self.project_dir)
		has_any = False
		tpl_dir = join(USER_DIR, "templates", template)
		if not exists(tpl_dir):
			pe("exception", "missing_template", template)
			exit(1)
		if merge_directories(tpl_dir, self.project_dir, None, force, True):
			has_any = True
		if merge_directories(SCRIPT_DIR, self.project_dir, None, True, True):
			has_any = True
		for d in PROJECT_DIRS:
			path = join(self.project_dir, d)
			mkdirp(path)
		if not has_any:
			pe("notice", "init", "nothing")
		else:
			write_file(join(self.project_dir, ".template"), template)
		return True

	#------------------------------
	# Update
	#------------------------------

	# Make upgrade and build flags of the same iterative action to save cycles

	def update(self):
		pe("action", "update", self.project_dir)
		self._handle_project_dependencies()

	#------------------------------
	# Build
	#------------------------------

	def _build(self, output_dir, skip=False, single=False, rawsrc=False):
		if self.update_project:
			pe("action", "update", self.project_dir)
		self._prepare()
		self.build_project = True
		self.single_file = single
		self.rawsrc = rawsrc
		self.output_dir = realpath(output_dir)
		mkdirp(self.output_dir)
		self._handle_project_dependencies()

	def build(self, output_dir, skip=False, single=False, rawsrc=False):
		self.current_manifest = self.project_manifest
		self.manifest = get_json(self.project_manifest)
		if "build_targets" in self.manifest:
			build_idx = 0
			for target in self.manifest["build_targets"]:
				self.update_project = build_idx == 0 and not skip
				bm = BUILD_TARGET.format(self.project_dir, target)
				self.current_manifest = bm
				self.manifest = get_json(bm)
				self._build(output_dir, skip, single, rawsrc)
				build_idx += 1
		else:
			self.update_project = not skip
			self._build(output_dir, skip, single, rawsrc)

