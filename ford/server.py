#!/usr/bin/env python

import socket, os
from os import chdir
from SocketServer import BaseServer, TCPServer, ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SimpleHTTPServer import SimpleHTTPRequestHandler
from OpenSSL import SSL
from threading import Thread

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
	pass

def serve_on_port(port, dest=None):
	if port == 443:
		secure()
	else:
		if dest is not None:
			chdir(dest)
		server = ThreadingHTTPServer(("",port), SimpleHTTPRequestHandler)
		server.serve_forever()

def threaded(port=8080, dest=None):
	try:
		Thread(target=serve_on_port, args=[port, dest]).start()
	except KeyboardInterrupt:
		pass

def simple(port=8080):
	server = HTTPServer(("", port), SimpleHTTPRequestHandler)
	sa = server.socket.getsockname()
	print "Serving HTTP on", sa[0], "port", sa[1], "..."
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass

'''
SimpleSecureHTTPServer.py - simple HTTP server supporting SSL.

- replace fpem with the location of your .pem server file.
- the default port is 443.

usage: python SimpleSecureHTTPServer.py
from: http://code.activestate.com/recipes/442473-simple-http-server-supporting-ssl-secure-communica/
'''

class SecureHTTPServer(HTTPServer):
	def __init__(self, server_address, HandlerClass):
		BaseServer.__init__(self, server_address, HandlerClass)
		ctx = SSL.Context(SSL.SSLv23_METHOD)
		#server.pem's location (containing the server private key and
		#the server certificate).
		fpem = os.path.expanduser('~/.ford/localhost.pem')
		try:
			ctx.use_privatekey_file (fpem)
		except SSL.Error:
			print "There seems to be a problem with your ford SSL cert"
			print "Please regenerate this cert by running: "
			print "\n\tford mkcert\n"
			exit(1)
		ctx.use_certificate_file(fpem)
		self.socket = SSL.Connection(ctx, socket.socket(self.address_family,
														self.socket_type))
		self.server_bind()
		self.server_activate()

	def shutdown_request(self,request):
		request.shutdown()

class SecureHTTPRequestHandler(SimpleHTTPRequestHandler):
	def setup(self):
		self.connection = self.request
		self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
		self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)

def secure(HandlerClass = SecureHTTPRequestHandler,
		 ServerClass = SecureHTTPServer):
	server_address = ('', 443) # (address, port)
	httpd = ServerClass(server_address, HandlerClass)
	sa = httpd.socket.getsockname()
	print "Serving HTTPS on", sa[0], "port", sa[1], "..."
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass

