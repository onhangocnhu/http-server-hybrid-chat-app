#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.request
~~~~~~~~~~~~~~~~~

This module provides a Request object to manage and persist 
request settings (cookies, auth, proxies).
"""
from .dictionary import CaseInsensitiveDict
import json as _json
from urllib.parse import urlparse, urlencode

PROXY_IP = "127.0.0.1"
PROXY_PORT = 8080

class Request():
    """The fully mutable "class" `Request <Request>` object,
    containing the exact bytes that will be sent to the server.

    Instances are generated from a "class" `Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    Usage::

      >>> import deamon.request
      >>> req = request.Request()
      ## Incoming message obtain aka. incoming_msg
      >>> r = req.prepare(incoming_msg)
      >>> r
      <Request>
    """
    __attrs__ = [
        "method",
        "url",
        "headers",
        "body",
        "reason",
        "cookies",
        "body",
        "routes",
        "hook",
        "json",
        "form"
    ]

    def __init__(self):
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None
        #: HTTP path
        self.path = None        
        # The cookies set used to create Cookie header
        self.cookies = None
        #: request body to send to the server.
        self.body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None
        # request json to send to the server
        self.json = None
        # request form to send to the server
        self.form = None

    def extract_request_line(self, request):
        try:
            lines = request.splitlines()
            first_line = lines[0]
            method, path, version = first_line.split()
            if path == '/':
                path = '/index' # default
            elif path == '/submit-info' and method == 'GET':
                path = '/chat.html'
        except Exception:
            return None, None

        return method, path, version

    def prepare_headers(self, request):
        """Prepares the given HTTP headers."""
        lines = request.split('\r\n')
        headers = {}
        for line in lines[1:]:
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key.lower()] = val 
        return headers
    
    def prepare(self, request, routes=None):
        """Prepares the entire request with the given parameters."""
        # parse method, path, version
        self.method, self.path, self.version = self.extract_request_line(request)
        self.headers = CaseInsensitiveDict(self.prepare_headers(request))
        
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

        # routing
        if routes:
            self.routes = routes
            self.hook = routes.get((self.method, self.path))

        # cookie authentication
        cookies = self.headers.get('Cookie', '')
        self.prepare_cookies(cookies)

        try:
            parts = request.split("\r\n\r\n", 1)
            if len(parts) > 1:
                body_str = parts[1]
                ctype = self.headers.get("Content-Type", "")
                if "application/json" in ctype.lower():
                    try:
                        parsed_body = _json.loads(body_str)
                    except Exception:
                        parsed_body = {}
                    self.prepare_body(json=parsed_body)
                elif "application/x-www-form-urlencoded" in ctype.lower():
                    # "username=admin&password=secret"
                    list_form = body_str.split('&')
                    parsed_body = {}
                    for part in list_form:
                        k, v = part.split('=', 1)
                        parsed_body[k] = v
                    self.prepare_body(data=parsed_body)
                elif body_str.strip():
                    self.prepare_body(data=body_str)

        except Exception as e:
            print("[Request] Failed to parse body:", e)
            self.body = None
            self.json = None
            self.form = None

        return self
    
    def prepare_body(self, data=None, files=None, json=None):
        """
        Normalize and set request body bytes and related parsed structures.
        - data: dict (form) or bytes/str raw body
        - files: not fully implemented (fallback to raw bytes)
        - json: python object -> serialized to JSON
        """
        body_bytes = b""
        if json:
            self.json = json
            body_bytes = _json.dumps(json).encode("utf-8")
            self.headers['Content-Type'] = 'application/json'
        # data can be: form, text
        elif data:
            if isinstance(data, dict) or isinstance(data, CaseInsensitiveDict):
                body_bytes = urlencode(data).encode('utf-8')
                self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
                self.form = data
            elif isinstance(data, (bytes, bytearray)):
                body_bytes = bytes(data)
                self.headers['Content-Type'] = 'application/octet-stream'
            elif isinstance(data, str):
                body_bytes = data.encode('utf-8')
                self.headers['Content-Type'] ='text/plain'
            else:
                body_bytes = b''
        elif files:
            if isinstance(files, (bytes, bytearray)):
                body_bytes = bytes(files)
            else:
                body_bytes = str(files).encode("utf-8")
            self.headers['Content-Type'] = 'multipart/form-data'

        # assign and update content-length
        self.body = body_bytes
        self.prepare_content_length(self.body)
        return 
    
    def prepare_content_length(self, body):
        """Ensure Content-Length header matches the provided body bytes."""
        #
        # TODO prepare the request content-length
        #
        try:
            length = len(body) if body is not None else 0
        except Exception:
            length = 0
        self.headers['Content-Length'] = str(length)
        return

    def prepare_auth(self, auth, url=""):
        #
        # TODO prepare the request authentication
        #
        import base64

        if not auth:
            return

        # basic: tuple (username, password)
        if isinstance(auth, tuple) and len(auth) == 2:
            user, pwd = auth
            token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
            self.headers['Authorization'] = f"Basic {token}"
            return

        # if isinstance(auth, str):
        #     if auth.lower().startswith('bearer ') or auth.lower().startswith('basic '):
        #         self.headers['Authorization'] = auth
        #     else:
        #         self.headers['Authorization'] = f"Bearer {auth}"
        return

    def prepare_cookies(self, cookies):
        ret_cookie = {}
        for c_part in cookies.split(';'):
            if '=' in c_part:
                k, v = c_part.strip().split('=', 1)
                ret_cookie[k] = v
        self.cookies = ret_cookie
        return

    def send(self, method="GET", url="", headers=None, data=None, files_data=None, json_data=None, timeout=5, useProxy=True):
        import socket

        parsed_url = urlparse(url)
        host = parsed_url.hostname
        port = parsed_url.port or 80
        path = parsed_url.path or "/"

        print(f"[Request] url: {url} with hostname {host} and port {port}")

        headers = headers or {}
        if not self.headers:
            self.headers = headers

        if json_data:
            self.prepare_body(json=json_data)
        elif files_data:
            self.prepare_body(files=files_data)
        elif data:
            self.prepare_body(data=data)
        else:
            self.body = b""

        headers["Host"] = host
        headers["Connection"] = "close"
        headers["Content-Length"] = str(len(self.body))

        if useProxy:
            dest = (PROXY_IP, PROXY_PORT)
        else:
            dest = (host, port)

        request_data = (
            f"{method} {path} HTTP/1.1\r\n" +
            "".join(f"{k}: {v}\r\n" for k, v in headers.items()) +
            "\r\n"
        ).encode("utf-8") + self.body

        with socket.create_connection(dest, timeout=timeout) as sock:
            sock.sendall(request_data)
            sock.shutdown(socket.SHUT_WR)
            response = b""
            while chunk := sock.recv(4096):
                response += chunk

        return response.decode("utf-8", errors="ignore")
