/**
 * Bootstrap
 *
 * Copyright (c) 2012 Knewton
 * Dual licensed under:
 *  MIT: http://www.opensource.org/licenses/mit-license.php
 *  GPLv3: http://www.opensource.org/licenses/gpl-3.0.html
 */
/*jslint browser: true, maxerr: 50, indent: 4, maxlen: 79, regexp: true */
(function () {
	"use strict";

	//------------------------------
	//
	// Constants
	//
	//------------------------------

	//------------------------------
	// Regular expressions
	//------------------------------

		/**
		 * Matches local protocols.
		 * @type {RegExp}
		 */
	var RX_LOCAL = /^(about|app|app\-storage|.+\-extension|file|res|widget):$/,

		/**
		 * Image path replacement.
		 * @type {RegExp}
		 */
		RX_IMAGE = /url\(["']?images\/([^'")]*)["']?\)/g,

		/**
		 * Used to remove the cache buster from a URL.
		 * @type {RegExp}
		 */
		RX_CACHEBUST = /_=[0-9]+/,

	//------------------------------
	//
	// Properties
	//
	//------------------------------

	//------------------------------
	// System
	//------------------------------

		/**
		 * Detemrine if the dom is ready.
		 */
		isDomReady = false,

		/**
		 * Have all resources been processed?
		 * @type {boolean}
		 */
		allResourcesProcessed = false,

		/**
		 * Did the system pause jQuery's ready event?
		 */
		pause = false,

		/**
		 *	The head of this document.
		 */
		head = document.getElementsByTagName('head')[0],

		/**
		 * The script tag which included the bootstrap.
		 * @type {HTMLElement}
		 */
		root = document.getElementById("bootstrap"),

		/**
		 * If a script is pending load.
		 * @type {boolean}
		 */
		pendingLoad = false,

		/**
		 * Scripts pending load.
		 * @type {Array<Object<string, string|function()>}
		 */
		scripts = [],

		/**
		 * Listeners pending execution. Used for pulling in coffeescript
		 * interpreter.
		 * @type {Array<*>}
		 */
		waiting,

	//------------------------------
	// Application
	//------------------------------

		/**
		 * The application scripts which must be loaded.
		 * @type {Array<string>}
		 */
		appPending,

		/**
		 * The number of pending scripts and styles left to load.
		 */
		pendingIncludes = 0,

	//------------------------------
	// Library
	//------------------------------

		/**
		 * The number of resources pending loading in the system.
		 * @type {nubmer}
		 */
		pendingResources = 0,

		/**
		 * A list of all the stylesheets included.
		 * @type {Array<string>}
		 */
		css = [],

		/**
		 * A list of resources held by other resources for includes.
		 * @type {Object<string, Object<string, *>}
		 */
		heldResources = {},

		/**
		 * A list of defined libraries.
		 * @type {Object<string, Object<string, Array<string>>>}
		 */
		libraryDefinitions = {},

		/**
		 * A set of groups for each library.
		 * @type {Object<string, Object<string, Array<string>>>}
		 */
		libGroups = {},

		/**
		 * A list of included library resources.
		 * @type {Object<string, Array<string>>}
		 */
		includedResources = {},

		/**
		 * HTML Fragments to be inserted recursively before being loaded.
		 * @type {Object<string, Object<string, string>>}
		 */
		htmlFragments = {},

		/**
		 * A list of file paths which have already been included.
		 * @type {Object<string, boolean>}
		 */
		includedFiles = {},

	//------------------------------
	// Application
	//------------------------------

		/**
		 * The manifest for the current applciation.
		 * @type {Object<string, *>}
		 */
		applicationManifest;

	//------------------------------
	// Ready queue
	//------------------------------

		/**
		 * A queue of listeners to trigger when the bootstrap has loaded.
		 * @type{function()}
		 */
		window.onBootstrap = [];

	//------------------------------
	//
	// Methods
	//
	//------------------------------

	//------------------------------
	// Utilities
	//------------------------------

	/**
	 * Cleans up a URL for presentation.
	 * @param {string} url The url to clean.
	 * @return url The cleaned up url.
	 */
	function cleanURL(url) {
		url = url.replace(RX_CACHEBUST, "").replace("?&", "?");
		if (url.substr(-1) === "?") {
			url = url.substr(0, url.length - 1);
		}

		return url;
	}

	/**
	 * Takes the ["foo.", ["a", "b"]] shorthand and expands it into the
	 * object provided as {foo.a: ".", foo.b: "."} which includes each.
	 * @param {Array} shorthand The ["foo.", ["a", "b"]] shorthand array.
	 * @param {Object} obj The object to put the names into as dot includes.
	 */
	function expandNamespace(shorthand, obj) {
		var i;

		for (i = 0; i < shorthand[1].length; i++) {
			obj[shorthand[0] + shorthand[1][i]] = ".";
		}
	}

	/**
	 * Use the use_at declaration of an application manifest.
	 * @param {string} library The name to possibly convert.
	 */
	function replaceLibrary(library) {
		if (applicationManifest.use_as) {
			if (applicationManifest.use_as[library]) {
				return applicationManifest.use_as[library];
			}
		}
		return library;
	}

	/**
	 * Takes the "&" argument from a manifest and expands it out.
	 * @param {Array|Object} libs A list of libs.
	 */
	function expandLibs(libs) {
		var lib,
			exp,
			b, i, l;

		if (libs === undefined) {
			return;
		}

		if (libs instanceof Array) {
			b = {};
			for (i in libs) {
				l = replaceLibrary(libs[i]);
				if (l instanceof Array) {
					expandNamespace(l, b);
				} else {
					b[l] = ".";
				}
			}
			libs = b;
		}

		exp = libs["&"];

		if (exp !== undefined) {
			for (lib in exp) {
				if (exp.hasOwnProperty(lib)) {
					lib = replaceLibrary(exp[lib]);
					if (lib instanceof Array) {
						expandNamespace(lib, libs);
					} else {
						libs[lib] = ".";
					}
				}
			}

			delete libs["&"];
		}

		return libs;
	}

	function expandManifest(lib, m) {
		var newManifest = {},
			libResources = [],
			resources,
			k, v, gk,
			i;

		for (k in m) {
			if (m.hasOwnProperty(k)) {
				v = m[k];
				v.reqs = expandLibs(v.reqs);

				if (k.substr(0, 1) === "@") {
					if (v.resources) {
						resources = v.resources;
						gk = k.substr(1);
						if (libGroups[lib] === undefined) {
							libGroups[lib] = {};
						}
						libGroups[lib][gk] = resources;
						libResources = libResources.concat(resources);
						delete v.resources;

						for (i = 0; i < resources.length; i++) {
							newManifest[resources[i]] = v;
						}
					}

					continue;
				} else if (k !== "application") {
					libResources.push(k);
				}

				newManifest[k] = v;
			}
		}

		// Applications should depend on all their resources
		if (newManifest.application) {
			newManifest.application.reqs["."] = libResources;
		}

		return newManifest;
	}

	/**
	 * Returns the current unix timestamp.
	 * @return {number} The curren time.
	 */
	function now() {
		return (new Date()).valueOf();
	}

	/**
	 * Embeds a script.
	 * @param {string} path The path to the file to load.
	 * @param {function()} listener A listener.
	 */
	function embedScript(path, callback, fromQueue) {
		if (pendingLoad || (scripts.length > 0 && !fromQueue)) {
			scripts.push([
				path,
				callback,
				true // From queue
			]);
			return;
		}
		pendingLoad = true;
		var script = document.createElement("script"),
			done = false;

		// Attach handlers for all browsers
		script.onload = script.onreadystatechange = function () {
			var rs = this.readyState,
				s;
			if (!done && (!rs || rs === "loaded" || rs === "complete")) {
				done = true;

				// Handle memory leak in IE
				script.onload = script.onreadystatechange = null;
				if (script.parentNode) {
					head.removeChild(script);
				}

				pendingLoad = false;

				if (window.jQuery && !jQuery.isReady && jQuery.holdReady &&
						!pause) {
					pause = true;
					jQuery.holdReady(true);
				}

				if (callback !== undefined) {
					callback.call(callback, null, "js");
				}

				if (scripts.length > 0) {
					embedScript.apply(embedScript, scripts.shift());
				}
			}
		};

		script.setAttribute("type", "text/javascript");
		script.setAttribute("src", path + "?_=" + now());

		head.insertBefore(script, head.firstChild);
	}

	/**
	 * Handles the compilation of CoffeeScript. Used to provide a central place
	 * to handle errors.
	 * @param {string} src The coffeescript to compile.
	 * @param {string} path The path to the file (used in case of error).
	 */
	function csCompile(src, path) {
		try {
			CoffeeScript.eval(src);
		} catch (e) {
			throw ["CoffeeScript [", cleanURL(path), "]: ", e].join("");
		}
	}

	/**
	 * Triggered when the coffeescript interpreter is included. CoffeeScript
	 * should only get included when it's needed, meaning there should always
	 * be an item in the waiting listeners queue.
	 *
	 * Additionally, it's usually the case that DomReady has
	 * triggered well before the bootstrap includes the coffeescript
	 * processor. Run a bit of coffee script to "activate" any inline scripts.
	 */
	function csProcessor() {
		var listener = waiting[0],
			response = waiting[1],
			format = waiting[2],
			path = waiting[3];
		waiting = null;

		if (isDomReady) {
			// This kicks off the inline script evaluation for coffeescript
			// This needs be run only when coffeescript is included after the
			// DOM has readied.
			CoffeeScript.eval([
				"scripts = window.document.getElementsByTagName 'script'",
				"ctypes = ['text/coffeescript', 'text/literate-coffeescript']",
				"coffees = (s for s in scripts when s.type in ctypes)",
				"index = 0",
				"length = coffees.length",
				"do execute = ->",
				"  script = coffees[index++]",
				"  mt = script?.type",
				"  if mt in ctypes",
				"    options = {literate: mt is 'text/literate-coffeescript'}",
				"    if script.src",
				"      CoffeeScript.load script.src, execute, options",
				"    else",
				"      options.sourceFiles = ['embedded']",
				"      CoffeeScript.run script.innerHTML, options",
				"      execute()",
				"null"
			].join("\n"));
		}

		csCompile(response, path);
		listener.call(listener, response, format);
	}

	/**
	 * Performs a get request using AJAX.
	 * @param {string} path The path to the file to load.
	 * @param {function({string|Object|Array})} listener A listener.
	 * @param {string} format File type: json, css, js
	 */
	function get(path, listener, format) {
		var xhr,
			processor;

		format = format.toLowerCase();

		if (format === "js") {
			embedScript(path, listener);
		} else {
			processor = function () {
				if (xhr.readyState === 4) {
					var sCode, response, pathing = path.split("/"),
						triggerListener = true;
					pathing.pop();
					pathing = pathing.join("/");

					try {
						sCode = xhr.status;
					} catch (e) {
						sCode = -1;
					}

					try {
						response = xhr.responseText;
					} catch (e) {
						response = "";
					}

					switch (format) {

					case "json":
						try {
							response = JSON.parse(response);
						} catch (e) {
							throw cleanURL(path) + " is invalid JSON";
						}
						break;

					case "css":
						response = response.replace(RX_IMAGE,
							"url(" + pathing + "/images/$1)");
						break;

					case "coffee":
						if (!window.CoffeeScript) {
							triggerListener = false;
							get("coffee-script.js", csProcessor, "js");
						} else {
							csCompile(response, path);
						}
						break;

					}

					if (sCode >= 200 && sCode < 300 || sCode === 304) {
						if (triggerListener) {
							listener.call(listener, response, format);
						} else {
							waiting = [listener, response, format, path];
						}
					} else {
						throw [sCode.toString(), "Error:", cleanURL(path)]
								.join(" ");
					}
				}
			}

			try {
				xhr = new XMLHttpRequest();
			} catch (e) {
				xhr = new ActiveXObject("Microsoft.XMLHTTP");
			}

			path += ["?_", now()].join("=");
			xhr.open("GET", path, true);

			try {
				xhr.onreadystatechange = processor;
			} catch (ex) {
				xhr.onload = processor;
			}

			xhr.send(null);
		}
	}

	/**
	 * Replaces the element with a new replacement element.
	 * @param {HTMLElement} element The element to replace.
	 * @param {HTMLElement} replacement The element to replace with.
	 */
	function replaceElement(element, replacement) {
		var nextElement = element.nextSibling,
			parentElement = element.parentNode;

		parentElement.removeChild(element);
		if (replacement !== undefined) {
			if (nextElement) {
				nextElement.parentNode.insertBefore(replacement, nextElement);
			} else {
				parentElement.appendChild(replacement);
			}
		}
	}

	/**
	 * Returns the first index of the value in the array.
	 * @param {*} v The value to search for.
	 * @param {Array} a The array to search.
	 * @return {number} The first index of the value in the array.
	 */
	function indexOf(v, a) {
		var i;

		if (Array.prototype.indexOf) {
			return a.indexOf(v);
		} else {
			for (i = 0; i < a.length; i++) {
				if (a[i] === v) {
					return i;
				}
			}
		}

		return -1;
	}

	//------------------------------
	// Components
	//------------------------------

	/**
	 * Adds classes to the target from the element, exclusing special classes
	 * used by the system.
	 * @param {HTMLElement} element The element to extact classes from.
	 * @param {HTMLElement} target The element to add classes to.
	 */
	function mergeClasses(element, target) {
		var classes = element.getAttribute("class"),
			tClasses = target.getAttribute("class"),
			index,
			tIndex,
			newClass,
			add = [],
			inArray = false;

		if (!classes) {
			// If the element has no classes there's nothing to do.
			return;
		} else {
			classes = classes.split(" ");
		}

		if (!tClasses) {
			tClasses = [];
		}

		for (index = 0; index < classes.length; index++) {
			inArray = false;
			newClass = classes[index];
			if (newClass === "component") {
				continue;
			}

			if (indexOf(newClass, tClasses) !== -1) {
				add.push(newClass);
			}
		}

		if (add.length > 0) {
			target.setAttribute("class", add.join(" "));
		}
	}

	/**
	 * Replaces placeholders in the target with content from the element.
	 * @param {HTMLElement} element The element to extract content from.
	 * @param {HTMLElement} target The element to insert content into.
	 */
	function mergeSections(element, target) {
		var sectionMap = {},
			sections = element.getElementsByTagName("def"),
			tSections = target.getElementsByTagName("sect"),
			section,
			tSection,
			index,
			fragment,
			children,
			cIndex,
			child,
			targetSections;

		for (index = 0; index < sections.length; index++) {
			// Grab the IDs and create a map of defined sections
			section = sections[index];
			fragment = document.createDocumentFragment();
			children = Array.prototype.slice.call(section.childNodes);
			for (cIndex = 0; cIndex < children.length; cIndex++) {
				child = children[cIndex];
				fragment.appendChild(child);
			}
			sectionMap[section.getAttribute("class")] = fragment;
		}

		// We will be modifying the children as we go, so clone the array.
		tSections = Array.prototype.slice.call(tSections);

		for (index = 0; index < tSections.length; index++) {
			// Replace ever target section, even if no content is defined.
			// If no matching section is defined in the sectionMap, the
			// replaceElement method will simply remove the target section.
			tSection = tSections[index];
			replaceElement(tSection,
					sectionMap[tSection.getAttribute("class")]);
		}
	}

	function expandComponentGroups(component) {
		var id = component.getAttribute("id"),
			parts = id.split("@"),
			lib = parts.shift(),
			group = parts.join("@"),
			fragment,
			factory,
			index,
			groups = libGroups[lib],
			resources;

		if (groups === undefined || [group] === undefined) {
			throw lib + " contains no group (@" + group + ")";
		}

		resources = groups[group];
		fragment = document.createDocumentFragment();
		factory = document.createElement("div");
		for (index = 0; index < resources.length; index++) {
			factory.innerHTML = '<component id="' + lib + "-" +
					resources[index] + '"></component>';
			fragment.appendChild(factory.firstChild);
		}

		replaceElement(component, fragment);
	}

	/**
	 * Handles the insertion of component HTML into it's target element.
	 * @param {HTMLElement} component The component target location.
	 */
	function insertComponent(component) {
		var id = component.getAttribute("id"),
			parts = id.split("-"),
			lib = parts.shift(),
			resource = parts.join("-"),
			content,
			factory,
			element;

		if (htmlFragments[lib] === undefined ||
				htmlFragments[lib][resource] === undefined) {
			throw lib + " contains no fragments (" + resource + ")";
		}

		content = htmlFragments[lib][resource];
		factory = document.createElement("div");
		factory.innerHTML = content;
		element = factory.firstChild;

		mergeClasses(component, element);
		mergeSections(component, element);

		replaceElement(component, element);
	}

	/**
	 * Locates any component tags with class .component and replaces them
	 * with their defined content. The id of the tags should be in the format
	 * "lib_name-resource_name".
	 *
	 * Optional section def tags can be used within the component tag to insert
	 * application-specific HTML into a correspondingly identified section
	 * tag within the content HTML. The class of the def tags must match
	 * the class of a sect tag within the component to be replaced.
	 */
	function resolveComponents() {
		var g = document.getElementsByTagName("group"),
			c,
			index;

		g = Array.prototype.slice.call(g);
		for (index = 0; index < g.length; index++) {
			expandComponentGroups(g[index]);
		}

		// Convert from a node list before modifying
		c = document.getElementsByTagName("component"),
		c = Array.prototype.slice.call(c);

		for (index = 0; index < c.length; index++) {
			insertComponent(c[index]);
		}

		// Recursively inject components
		if (document.getElementsByTagName("component").length > 0 ||
			document.getElementsByTagName("group").length > 0) {
			resolveComponents();
		}
	}

	//------------------------------
	// Pathing
	//------------------------------

	/**
	 * Creates a path from the provided arguments.
	 * @param {...*} var_args Path parts to combine.
	 */
	function mkpath() {
		return Array.prototype.slice.apply(arguments).join("/");
	}

	/**
	 * Returns a path to a library.
	 * @param {string} library The library to fetch a path for.
	 * @return {string} The library path.
	 */
	function libraryPath(library) {
		return "lib/" + library;
	}

	/**
	 * Completes the bootstrapping process.
	 */
	function complete() {
		var s,
			index;
		if (css.length > 0) {
			s = document.createElement("style");
			s.setAttribute("type", "text/css");
			s.setAttribute("media", "screen, print");
			s.innerHTML = css.join("");
			head.insertBefore(s, head.lastChild);
		}
		resolveComponents();
		window.__bootstrapped__ = true;
		if (pause) {
			jQuery.holdReady(false);
		}
		for (index = 0; index < window.onBootstrap.length; index++) {
			window.onBootstrap[index]();
		}
	}

	//------------------------------
	// Application
	//------------------------------

	/**
	 * Mark an application resource as included.
	 */
	function appIncluded() {
		pendingIncludes -= 1;
		if (pendingIncludes <= 0) {
			complete();
		}
	}

	/**
	 * Incldues the next application script.
	 * @param {boolean} first If this is the first time called.
	 */
	function includeAppScript(first) {
		if (!Boolean(first)) {
			appIncluded();
		}

		if (appPending.length > 0) {
			get(appPending.shift() + ".js", includeAppScript, "js");
		}
	}

	function missingLibs() {
		var missing = false,
			lib;

		for (lib in libraryDefinitions) {
			if (libraryDefinitions.hasOwnProperty(lib)) {
				if (libraryDefinitions[lib] === null) {
					missing = true;
					return false;
				}
			}
		}

		return missing;
	}

	/**
	 * Includes application resources.
	 */
	function loadApplicationResources() {
		if (!allResourcesProcessed || missingLibs()) {
			return;
		}

		var app,
			sIndex;
		if (applicationManifest.application !== undefined) {
			app = applicationManifest.application;
			if (app.scripts !== undefined && app.scripts.length > 0) {
				appPending = app.scripts;
				pendingIncludes += app.scripts.length;
				includeAppScript(true);
			}

			if (app.styles !== undefined && app.styles.length > 0) {
				pendingIncludes += app.styles.length;
				for (sIndex in app.styles) {
					get(app.styles[sIndex] + ".css", function (d) {
						css.push(d);
						appIncluded();
					}, "css");
				}
			}
		}

		if (pendingIncludes === 0) {
			complete();
		}
	}

	//------------------------------
	// Library
	//------------------------------

	/**
	 * Returns whether or not a resource has been includeed from a library.
	 * @param {string} library The library to load the resource from.
	 * @param {string} resource The resource to load.
	 * @return {boolean} If the resource has been included.
	 */
	function hasIncludedLibraryResource(library, resource) {
		var libResource;

		if (includedResources[library] === undefined) {
			includedResources[library] = {};
		}

		libResource = includedResources[library][resource];
		return libResource !== undefined && libResource.included;
	}

	/**
	 * Returns a list of missing requirements.
	 * @param {Object<string, Object<string, Array<string>>>} requirements
	 * @param {string} pendingLib The library of the resource pending loading.
	 * @param {string} pendingResource The resource pending loading.
	 * @return {Object<string, *>} The missing requirements object.
	 */
	function missingRequirements(requirements, pendingLib, pendingResource) {
		var missing = {
				length: 0,
				resources: {},
				order: []
			},
			lib,
			requiredResources,
			rIndex,
			resource,
			b, i;

		for (lib in requirements) {
			if (requirements.hasOwnProperty(lib)) {
				requiredResources = requirements[lib];

				// In reqs, a 'dot' as a project name means 'use my project'
				if (lib === ".") {
					lib = pendingLib;
				}

				if (heldResources[lib] === undefined) {
					heldResources[lib] = {};
				}

				if (requiredResources === "." || requiredResources === "*") {
					requiredResources = [lib];
				}

				for (rIndex in requiredResources) {
					if (requiredResources.hasOwnProperty(rIndex)) {
						resource = requiredResources[rIndex];
						if (!hasIncludedLibraryResource(lib, resource)) {
							if (missing.resources[lib] === undefined) {
								missing.order.push(lib);
								missing.resources[lib] = [];
							}

							if (heldResources[lib][resource] === undefined) {
								heldResources[lib][resource] = {};
							}

							if (heldResources[lib][resource][pendingLib] ===
								undefined) {
								heldResources[lib][resource][pendingLib] = [];
							}

							heldResources[lib][resource][pendingLib]
								.push(pendingResource);

							missing.resources[lib].push(resource);
							missing.length += 1;
						}
					}
				}
			}
		}

		return missing;
	}

	/**
	 * Removes an included library from the holding array of other resources.
	 * @param {Object<string, Array<string>} from The held resources.
	 * @param {string} library The library to load the resource from.
	 * @param {string} resource The resource to load.
	 */
	function removeResourceHold(from, library, resource) {
		if (from === undefined) {
			return;
		}

		var lib,
			rIndex,
			rsc,
			pendingLib,
			pendingResources,
			heldLib,
			hIndex;

		for (lib in from) {
			if (from.hasOwnProperty(lib)) {
				for (rIndex in from[lib]) {
					rsc = from[lib][rIndex];
					pendingLib = includedResources[lib][rsc];
					pendingResources = pendingLib.requires.resources;
					for (heldLib in pendingResources) {
						if (pendingResources.hasOwnProperty(heldLib) &&
							heldLib === library) {
							for (hIndex in pendingResources[heldLib]) {
								if (pendingResources[heldLib][hIndex] ===
									resource) {
									pendingLib.requires.length -= 1;
									delete pendingResources[heldLib][hIndex];
									break;
								}
							}
						}
					}
				}
			}
		}
	}

	/**
	 * Finishes the include of a library.
	 * @param {string} library The library to load the resource from.
	 * @param {string} resource The resource to load.
	 */
	function resourceIncluded(library, resource) {
		var libraryResource = includedResources[library][resource];

		libraryResource.loading = false;
		libraryResource.included = true;

		if (heldResources[library] !== undefined) {
			removeResourceHold(heldResources[library][resource], library,
							resource);
			loadResources(heldResources[library][resource]);
		}
		pendingResources -= 1;
		if (pendingResources === 0) {
			loadApplicationResources();
		}
	}

	/**
	 * Include a resource, based on its composition.
	 * @param {string} library The library to load the resource from.
	 * @param {string} resource The resource to load.
	 * @param {Array<string>} composition The composition of the resource.
	 */
	function include(library, resource, composition) {
		var	path = mkpath(libraryPath(library), resource, resource),
			cIndex,
			fileType,
			filePath,
			resource,
			pending = 0,
			hadPending = false;
		for (cIndex in composition) {
			fileType = composition[cIndex];
			if (fileType === "images") {
				continue;
			}
			filePath = path + "." + fileType;
			if (includedFiles[filePath] === undefined) {
				hadPending = true;
				includedFiles[filePath] = true;
				pending += 1;
				get(filePath, function (d, ft) {
					pending -= 1;
					switch (ft) {

					case "js":
						// noop
						break;

					case "css":
						css.push(d);
						break;

					case "html":
						if (htmlFragments[library] === undefined) {
							htmlFragments[library] = {};
						}
						htmlFragments[library][resource] = d;
						break;

					}

					if (pending <= 0) {
						resourceIncluded(library, resource);
					}
				}, fileType);
			}
		}

		if (!hadPending) {
			resourceIncluded(library, resource);
		}
	}

	/**
	 * Includes a resource from a library.
	 * @param {string} library The library to load the resource from.
	 * @param {string} resource The resource to load.
	 */
	function includeLibraryResource(library, resource) {
		var definition = libraryDefinitions[library][resource],
			libraryResource;

		if (definition === undefined) {
			throw [library, "does not contain resource:", resource].join(" ");
		}

		if (includedResources[library][resource] === undefined) {
			includedResources[library][resource] = {
				included: false,
				loading: false,
				requires: missingRequirements(definition.reqs, library,
												resource)
			};
			pendingResources += 1;
		}

		libraryResource = includedResources[library][resource];

		if (!libraryResource.included) {
			if (libraryResource.requires.length > 0) {
				loadResources(libraryResource.requires.resources,
						libraryResource.requires.order);
			} else {
				if (!libraryResource.loading) {
					libraryResource.loading = true;
					include(library, resource, definition.comp);
				}
			}
		}
	}

	/**
	 * Includes resources from a library.
	 * @param {string} library The library to load the resources from.
	 * @param {Array<string>} resources A list of resources to load.
	 * @param {string?} replaced The replacement lib string.
	 */
	function includeLibraryResources(library, resources, replaced) {
		var resource;

		replaced = library;
		library = replaceLibrary(library);
		if (replaced === library) {
			replaced = null;
		}

		if (resources === "." || resources === "*") {
			resources = [library];
		}

		if (!libraryDefinitions[library]) {
			// This begins undefined, then we set it to null to prevent double
			// requested. We fall into this block as long as it remains null.
			if (libraryDefinitions[library] === null) {
				return;
			}
			libraryDefinitions[library] = null;
			includedResources[library] = {};
			resource = mkpath(libraryPath(library), "manifest.json");
			get(resource, function (d) {
				libraryDefinitions[library] = expandManifest(library, d);
				includeLibraryResources(library, resources, replaced);
			}, "json");
		} else {
			for (resource in resources) {
				if (resources.hasOwnProperty(resource)) {
					resource = resources[resource];
					if (replaced === resource) {
						resource = library;
					}
					includeLibraryResource(library, resource);
				}
			}
		}
	}

	/**
	 * Wraps {@code includeLibraryResources()}.
	 * @param {Object<string, Array<string>} libraries Resources to include,
	 * @param {Array<string>} order The order to use the libraries in.
	 * @param {boolean} proceedIfEmpty Continue bootstrapping if empty.
	 */
	function loadResources(libraries, order, proceedIfEmpty) {
		var lib,
			index,
			hasAnyResources = false;

		libraries = expandLibs(libraries);

		if (order !== undefined) {
			for (index in order) {
				lib = order[index];
				if (libraries.hasOwnProperty(lib)) {
					hasAnyResources = true;
					includeLibraryResources(lib, libraries[lib]);
				}
			}
		} else {
			for (lib in libraries) {
				if (libraries.hasOwnProperty(lib)) {
					hasAnyResources = true;
					includeLibraryResources(lib, libraries[lib]);
				}
			}
		}

		allResourcesProcessed = true;

		if (!hasAnyResources && Boolean(proceedIfEmpty)) {
			loadApplicationResources();
		}
	}

	//------------------------------
	// Application
	//------------------------------

	/**
	 * Loads the application manifest.
	 * @param {Object<string, *>} manifest The application manifest.
	 */
	function loadApplication(manifest) {
		applicationManifest = manifest;
		loadResources(manifest.includes, undefined, true);
	}

	//------------------------------
	//
	// Event bindings
	//
	//------------------------------

	if (window.addEventListener) {
		window.addEventListener("DOMContentLoaded", function () {
			isDomReady = true;
		}, false);
	} else {
		window.attachEvent("onload", function () {
			isDomReady = true;
		});
	}

	//------------------------------
	//
	// Activation
	//
	//------------------------------

	// Attempt to activiate the boostrap
	if (RX_LOCAL.test(window.location.protocol)) {
		alert("The bootstrap cannot function over local protocols.");
	} else if (root === null) {
		alert('The tag including the bootstrap must have id="bootstrap"');
	} else {
		get("manifest.json", loadApplication, "json");
	}

}());

