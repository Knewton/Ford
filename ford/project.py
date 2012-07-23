#!/usr/bin/env python
from sys import exit
from json import dumps, loads
from os import makedirs, remove
from os.path import (realpath, exists, isfile, isdir, join, expanduser,
	dirname, basename, splitext)
from time import time
from shutil import copyfile, copytree, rmtree
from BeautifulSoup import BeautifulSoup, Tag
from utilities import mkdirp, read_file, write_file, call, merge_directories
from urllib2 import urlopen, HTTPError

#------------------------------
#
# Constants
#
#------------------------------

#------------------------------
# System paths
#------------------------------

USER_DIR = expanduser("~/.ford")
SCRIPT_DIR = join(USER_DIR, "scripts")

#------------------------------
# Upgrade
#------------------------------

SRC_DIR = dirname(__file__)
TARGETS = ["templates", "manifests", "scripts"]

#------------------------------
# Init
#------------------------------

DEFAULT_TEMPLATE = "web-application"
PROJECT_DIRS = ["lib", "manifests"]

#------------------------------
# Update and Build
#------------------------------

VALID_COMPS = ["html", "css", "js", "images"]

#------------------------------
# Excptions
#------------------------------

class UpdateError(Exception):
	pass

#------------------------------
#
# Utilities
#
#------------------------------

#------------------------------
# Generic
#------------------------------

def get_json(fp):
	if not exists(fp):
		print "File '{0}' does not exist!".format(fp)
		exit(1)
	try:
		return loads(read_file(fp))
	except ValueError:
		print "File '{0}' not valid JSON!".format(fp)
		exit(1)

def get_manifest(lib):
	return get_json("{0}/manifest.json".format(lib))

def split_uri(uri):
	# use git for blah.com/foo.git
	if uri[-4:] == ".git":
		protocol = "git"
		if "://" in uri:
			p, uri = uri.split("://")
		uri = uri[:-4]
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
		port, fp = path.split("/")
		if not port.isdigit():
			protocol = "git"
	# everything else should be file
	else:
		protocol = "file"
		# Handle ~ in the path
		uri = expanduser(uri)
	return protocol, uri

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

def upgrade(force=False):
	print "Ford upgrade:"
	if not merge_directories(SRC_DIR, "~/.ford", TARGETS, force):
		print "Nothing upgraded."
	print ""

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

	def __init__(self, project_dir):
		# Define properties
		self.project_dir = realpath(project_dir)
		self.output_dir = None
		self.libraries = {}
		self.included = {}
		self.held_resources = {}
		self.pending_resources = 0
		self.content = {"html": {}, "css": [], "js": []}
		self.manifest = None
		self.build_project = False
		self.update_project = True

	#------------------------------
	#
	# Internal methods
	#
	#------------------------------

	#------------------------------
	# Builder utilities
	#------------------------------

	def _compile(self, ftype):
		cmd = ["juicer", "merge", "--force", "--document-root",
				self.project_dir]
		src_file = "{0}/application.{1}".format(self.output_dir, ftype)
		if ftype == "js":
			cmd += ["--skip-verification"]
		elif ftype == "css":
			cmd += ["--force-image-embed"]
		cmd += [src_file]
		if call(cmd) == 0:
			remove(src_file)
		else:
			print "Error compiling {0}".format(src_file)
			exit(1)

	def _insert_component(self, component):
		cid = component["id"]
		parts = cid.split("-")
		lib = parts.pop(0)
		resource = "-".join(parts)
		html = self.content["html"]
		if not lib in html:
			print "{0} contains no html fragments!".format(lib)
			exit(1)
		if not resource in html[lib]:
			print "{0} {1} missing an html fragment!".format(lib, resource)
			exit(1)

		element = BeautifulSoup(html[lib][resource])
		merge_classes(component, element)
		merge_sections(component, element)
		replace_element(component, element)

	def _resolve_component_html(self, doc):
		components = doc.findAll("component")
		for c in components:
			self._insert_component(c)
		doc = BeautifulSoup(str(doc))
		if len(doc.findAll("component")) > 0:
			self._resolve_component_html(doc)
		return doc

	def _complete(self):
		if self.update_project:
			print ""

		print "Ford build:"
		path = "{0}/application".format(self.output_dir)
		has_css, has_js = False, False
		if len(self.content["css"]):
			css = []
			for p in self.content["css"]:
				css.append("@import url(/{1})".format(self.project_dir, p))
			write_file("{0}.css".format(path), "\n".join(css) + "\n")
			self._compile("css")
			has_css = True

		if len(self.content["js"]):
			js = []
			for p in self.content["js"]:
				js.append(" * @depends /{1}".format(self.project_dir, p))
			content = "/**\n{0}\n */\n".format("\n".join(js))
			write_file("{0}.js".format(path), content)
			self._compile("js")
			has_js = True

		index = "{0}/index.html"
		src = index.format(self.project_dir)
		if not exists(src):
			print "{0} does not exist!".format(src)
			exit(1)
		index_html = BeautifulSoup(read_file(src))

		bootstrap = index_html.findAll(id="bootstrap")
		if len(bootstrap) == 0:
			print "index.html has no script tag with id 'bootstrap'"
			exit(1)
		bootstrap = bootstrap[0]
		index_idx = bootstrap.parent.contents.index(bootstrap)

		if has_js:
			script = Tag(index_html, "script")
			script["type"] = "text/javascript"
			script["src"] = "application.min.js?_={0}".format(str(time()))
			bootstrap.parent.insert(index_idx + 1, script)

		if has_css:
			style = Tag(index_html, "link")
			style["media"] = "screen, print"
			style["rel"] = "stylesheet"
			style["type"] = "text/css"
			style["href"] = "application.min.css?_={0}".format(str(time()))
			bootstrap.parent.insert(index_idx + 1, style)

		# Remove the bootstrap tag
		bootstrap.extract()

		# Handle component HTML
		index_html = self._resolve_component_html(index_html)

		write_file(index.format(self.output_dir), str(index_html))

		loc = "{0}/localization"
		if exists(loc.format(self.project_dir)):
			if exists(loc.format(self.output_dir)):
				rmtree(loc.format(self.output_dir))
			copytree(loc.format(self.project_dir), loc.format(self.output_dir))

	#------------------------------
	# Dependency management
	#------------------------------

	def _make_git(self, rm=False):
		fp = join(self.project_dir, "tmp")
		if rm:
			return #todo!
			if exists(fp):
				rmtree(fp)
		elif not exists(fp):
			mkdirp(fp)
		return fp

	def _clean_git(self):
		self._make_git(True)

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
		if self.update_project:
			self._clean_git()

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
			if not lib in self.held_resources:
				self.held_resources[lib] = {}

			req_resources = reqs[lib]
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

	def _get(self, lib, resource, protocol, uri, ftype, fp=None, img=None):
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
			tmp = self._make_git()
			repo = join(tmp, resource)
			if not isdir(repo):
				url = "://".join([protocol, uri])
				call(["git", "clone", url, repo])
			protocol = "file"
			uri = join(repo, fp)
			fp = None

		if fp is not None:
			uri = "/".join([uri, fp])
		if ftype != "images":
			uroot, uext = splitext(uri)
			if uext == "":
				uri += ".{0}".format(ftype)

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
		err = "Error in {0} resource {1}:\n    ".format(lib, resource)

		dest = join(resource_path, fname)
		if protocol in ["http", "https"]:
			url = "://".join([protocol, uri])
			try:
				resp = urlopen(url)
				headers = resp.headers
				if ftype == "js":
					expected = "text/javascript"
				else:
					expected = "text/{0}".format(ftype)
				if not expected in headers["content-type"]:
					raise UpdateError(err +"{0} ({2}) not of type {1}".format(
						url, expected, headers["content-type"]))
				print "{0} => {1}".format(url, dest)
				write_file(dest, resp.read())
			except HTTPError as e:
				raise UpdateError(err + "{0} ({1})".format(str(e), url))
				exit(1)
		elif protocol == "file":
			if not isfile(uri):
				raise UpdateError(err + "{0} is not a file".format(uri))
				exit(1)
			try:
				copyfile(uri, dest)
				print "{0} => {1}".format(uri, dest)
			except IOError as e:
				raise UpdateError(err + "Error copying file {0}: {1}".format(
					uri, str(e)))

	def _update_resource(self, lib, resource, details):
		uri = None
		for f in ["uri", "url", "path"]:
			if f in details:
				uri = details[f]
				del details[f]
				break

		append_name = False
		if uri is None:
			protocol, uri = "http", ""
		else:
			protocol, uri = split_uri(uri)
			# If the string ends with a slash, assume we should add the name
			if uri[-1] == "/":
				append_name = True
				uri = uri[:-1]

		if not "comp" in details:
			print "No comp for {0} resource {1}".format(lib, resource)
			exit(1)

		comp = details["comp"]

		def handle_images(imgs):
			path = uri
			i = "images"
			if ftype == "images/":
				path = "{0}/images".format(uri)

			if hasattr(imgs, "keys"):
				for name in imgs.keys():
					img = imgs[name]
					self._get(lib, resource, protocol, path, i, img, name)
			else:
				for img in imgs:
					self._get(lib, resource, protocol, path, i, img)

		comp_err = "bad composition ({{0}}) for {0} resource {1}".format(lib,
			resource)

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
					self._get(lib, resource, protocol, uri, ftype, comp[ftype])
			details["comp"] = comps
		else:
			for ftype in comp:
				if not ftype in VALID_COMPS:
					raise UpdateError(comp_err.format(ftype))
				if ftype == "images":
					if not "images" in details:
						raise UpdateError(
							"{0} resource {1} has no images".format(lib,
								resource))
					handle_images(details["images"])
				else:
					fp = None
					if append_name:
						fp = "{0}.{1}".format(resource, ftype)
					self._get(lib, resource, protocol, uri, ftype, fp)

	def _update_library(self, lib):
		manifest_path = "{0}/manifests/{1}.json".format(self.project_dir, lib)
		if not exists(manifest_path):
			manifest_path = "{0}/manifests/{1}.json".format(USER_DIR, lib)
		manifest = get_json(manifest_path)
		try:
			for resource in manifest:
				self._update_resource(lib, resource, manifest[resource])
		except UpdateError as e:
			print str(e)
			exit(1)

		lib_manifest = join(self.project_dir, lib_path(lib), "manifest.json")
		write_file(lib_manifest, dumps(manifest))

	def _include_library_resource(self, lib, resource):
		manifest = self.libraries[lib]
		includes = self.included[lib]

		if not resource in manifest:
			print "{0} does not define resource {1}".format(lib, resource)
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
			self.libraries[lib] = get_manifest(lib_path(lib))
			self.included[lib] = {}
		for r in resources:
			self._include_library_resource(lib, r)

	def _load_resources(self, includes, proceed_if_empty=False):
		has_resources = False

		for lib in includes:
			has_resources = True
			self._include_library_resources(lib, includes[lib])

		if not has_resources and proceed_if_empty:
			self._load_application_reosurces()

	def _handle_project_dependencies(self):
		self.manifest = get_manifest(self.project_dir)
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

	def init(self, template=None, force=False):
		print "Ford init:"
		if template is None:
			template = DEFAULT_TEMPLATE

		has_any = False
		tpl_dir = join(USER_DIR, "templates", template)
		if not exists(tpl_dir):
			print "{0} is not a template".format(template)
			exit(1)
		if merge_directories(tpl_dir, self.project_dir, None, force, True):
			has_any = True
		if merge_directories(SCRIPT_DIR, self.project_dir, None, force, True):
			has_any = True
		for d in PROJECT_DIRS:
			path = join(self.project_dir, d)
			mkdirp(path)
		if not has_any:
			print "No actions."
		print ""

	#------------------------------
	# Update
	#------------------------------

	# Make upgrade and build flags of the same iterative action to save cycles

	def update(self):
		print "Ford update:"
		self._handle_project_dependencies()
		print ""

	#------------------------------
	# Build
	#------------------------------

	def build(self, output_dir, skip=False):
		if not skip:
			print "Ford update:"
		self.build_project = True
		self.update_project = not skip
		self.output_dir = realpath(output_dir)
		mkdirp(self.output_dir)
		self._handle_project_dependencies()
		print ""

