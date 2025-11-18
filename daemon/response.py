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
daemon.response
~~~~~~~~~~~~~~~~~

This module provides a :class: `Response <Response>` object to manage and persist 
response settings (cookies, auth, proxies), and to construct HTTP responses
based on incoming requests. 

The current version supports MIME type detection, content loading and header formatting
"""

from datetime import datetime, timezone, timedelta
import os
from .dictionary import CaseInsensitiveDict

# BASE_DIR = ""
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + os.sep

def join_path(base_dir: str, path: str):
    """
    Safe join base_dir + path.
    Returns valid absolute path or None if file not found.
    """
    abs_base = os.path.abspath(base_dir)
    file_path = os.path.abspath(os.path.join(abs_base, *path.strip('/').split('/')))
    print("[Response] Debug: joined file_path =", file_path)
    if not file_path.startswith(abs_base):
        print("[Response] Access denied outside base_dir:", file_path)
        return None
    if not os.path.isfile(file_path):
        print("[Response] File not found:", file_path)
        return None
    return file_path


def _json(data, code=200):
    import json
    r = Response()
    r.status_code = code
    r.headers["Content-Type"] = "application/json"
    r.content = json.dumps(data).encode("utf-8")
    r.headers["Access-Control-Allow-Origin"] = "*"
    return r

def handle_text_other(sub_type):
    if sub_type == 'csv':
        return 'static/'
    if sub_type == 'xml':
        return 'apps/'
    return 'static/'

class Response():   
    """The :class:`Response <Response>` object, which contains a
    server's response to an HTTP request.

    Instances are generated from a :class:`Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    :class:`Response <Response>` object encapsulates headers, content, 
    status code, cookies, and metadata related to the request-response cycle.
    It is used to construct and serve HTTP responses in a custom web server.

    :attrs status_code (int): HTTP status code (e.g., 200, 404).
    :attrs headers (dict): dictionary of response headers.
    :attrs url (str): url of the response.
    :attrsencoding (str): encoding used for decoding response content.
    :attrs history (list): list of previous Response objects (for redirects).
    :attrs reason (str): textual reason for the status code (e.g., "OK", "Not Found").
    :attrs cookies (CaseInsensitiveDict): response cookies.
    :attrs elapsed (datetime.timedelta): time taken to complete the request.
    :attrs request (PreparedRequest): the original request object.

    Usage::

      >>> import Response
      >>> resp = Response()
      >>> resp.build_response(req)
      >>> resp
      <Response>
    """

    __attrs__ = [
        "_content",
        "_header",
        "status_code",
        "method",
        "headers",
        "url",
        "history",
        "encoding",
        "reason",
        "cookies",
        "elapsed",
        "request",
        "body",
        "reason",
    ]


    def __init__(self, request=None):
        """
        Initializes a new :class:`Response <Response>` object.

        : params request : The originating request object.
        """

        self._content = False
        self._content_consumed = False
        self._next = None

        #: Integer Code of responded HTTP Status, e.g. 404 or 200.
        self.status_code = None

        #: Case-insensitive Dictionary of Response Headers.
        #: For example, ``headers['content-type']`` will return the
        #: value of a ``'Content-Type'`` response header.
        self.headers = {}

        #: URL location of Response.
        self._url = None

        #: Encoding to decode with when accessing response text.
        self.encoding = None

        #: A list of :class:`Response <Response>` objects from
        #: the history of the Request.
        self.history = []

        #: Textual reason of responded HTTP Status, e.g. "Not Found" or "OK".
        self.reason = None

        #: A of Cookies the response headers.
        self.cookies = CaseInsensitiveDict()

        #: The amount of time elapsed between sending the request
        self.elapsed = timedelta(0)

        #: The :class:`Request <Request>` object to which this
        #: is a response.
        self.request = request
    
    @property
    def content(self):
        """Return the raw bytes content of the response."""
        return self._content

    @content.setter
    def content(self, value):
        """Assign response content and auto-update Content-Length."""
        if isinstance(value, str):
            value = value.encode('utf-8')
        elif not isinstance(value, (bytes, bytearray)):
            raise TypeError("Response content must be bytes or string.")
        self._content = value
        self.prepare_content_length(value)
    
    @property
    def url(self):
        """Return redirect / target URL."""
        return self._url
    
    @url.setter
    def url(self, value):
        """Set redirect target and automatically add Location header."""
        self._url = value
        if value:
            self.headers['Location'] = value
    
    def redirect(self, location, status_code=302):
        self.status_code = status_code
        self.url = location
        self.content = b""
        self.headers['Content-Type'] = 'text/html'
        self.prepare_content_length(self.content)
        return self
    
    def get_mime_type(self, req) -> str:
        """
        Determines the MIME type of a file based on its path.

        :params req (Request): Request received.

        :rtype str: MIME type string (e.g., 'text/html', 'image/png').
        """
        path = req.path.lower().strip()
        hook = getattr(req, "hook", None)

        if req.method == "OPTIONS":
            return "text/plain"

        # /get-list returns json
        if path == '/get-list':
            return "application/json"
        if (
            (path in ("/", "/index", "/login") and req.method == "GET")
            and "." not in os.path.basename(path) 
        ):
            req.path = path.rstrip('/') + ".html"
            return "text/html"

        if req.method == "POST":
            if "login" in path:
                req.path = path.rstrip('/') + ".html"
            return "application/json"

        if path.endswith(".html"):
            return "text/html"
        elif path.endswith(".css"):
            return "text/css"
        elif path.endswith(".js"):
            return "application/javascript"
        elif path.endswith((".jpg", ".jpeg")):
            return "image/jpeg"
        elif path.endswith(".png"):
            return "image/png"
        elif path.endswith(".ico"):
            return "image/x-icon"
        elif path.endswith(".json"):
            return "application/json"
        elif path.endswith(".txt"):
            return "text/plain"

        if hook and req.method != "GET":
            return "application/json"
        
        return "text/html"
    
    def set_cookie(self, name, value, max_age=None, expires=None, secure=False, http_only=False):
        """
        Adds a cookie to the response.

        :param name: Cookie name
        :param value: Cookie value
        :param path: Path scope of the cookie (default '/')
        :param max_age: Optional lifetime in seconds
        :param expires: Optional absolute expiry date (as HTTP-date string)
        :param secure: If True, adds 'Secure' flag
        :param http_only: If True, adds 'HttpOnly' flag
        """
        if not hasattr(self, "cookies"):
            self.cookies = {}

        cookie_str = f"{value}"
        if max_age:
            cookie_str += f"; Max-Age={max_age}"
        if expires:
            cookie_str += f"; Expires={expires}"
        if secure:
            cookie_str += "; Secure"
        if http_only:
            cookie_str += "; HttpOnly"

        self.cookies[name] = cookie_str

    def prepare_content_type(self, mime_type='text/html'):
        """
        Prepares the Content-Type header and determines the base directory
        for serving the file based on its MIME type.

        :params mime_type (str): MIME type of the requested resource.

        :rtype str: Base directory path for locating the resource.

        :raises ValueError: If the MIME type is unsupported.
        """
        
        base_dir = ""

        main_type, sub_type = mime_type.split('/', 1)
        print("[Response] processing MIME main_type={} sub_type={}".format(main_type,sub_type))
        #
        #  TODO: process other mime_type
        #        application/xml       
        #        application/zip
        #        ...
        #        text/csv
        #        text/xml
        #        ...
        #        video/mp4 
        #        video/mpeg
        #        ...
        #
        if main_type == 'text':
            self.headers['Content-Type'] = 'text/{}'.format(sub_type)
            if sub_type == 'plain' or sub_type == 'css':
                base_dir = BASE_DIR + "static/"
            elif sub_type == 'html':
                base_dir = BASE_DIR + "www/"
            else:
                base_dir = BASE_DIR + handle_text_other(sub_type)
        elif main_type == 'image':
            if sub_type == 'x-icon':
                base_dir = BASE_DIR + "static/images"
            else:
                base_dir = BASE_DIR + "static/"
            self.headers['Content-Type'] = 'image/{}'.format(sub_type)
        elif main_type == 'application':
            if sub_type == 'javascript':
                base_dir = BASE_DIR + "static/"
            elif sub_type in ('json', 'xml'):
                base_dir = None
            else:
                base_dir = BASE_DIR + "apps/"
            self.headers['Content-Type'] = 'application/{}'.format(sub_type)
        
        else:
            raise ValueError("Invalid MEME type: main_type={} sub_type={}".format(main_type,sub_type))

        return base_dir

    def build_content(self, path, base_dir):
        """
        Loads the objects file from storage space.

        :params path (str): relative path to the file.
        :params base_dir (str): base directory where the file is located.

        :rtype tuple: (int, bytes) representing content length and content data.
        """
        if not base_dir:
            base_dir = BASE_DIR

        abs_base = os.path.abspath(base_dir)
        rel_path = path.lstrip('/\\')

        last = os.path.basename(os.path.normpath(abs_base))
        if last:
            prefix1 = last + os.sep
            prefix2 = last + '/'
            if rel_path.startswith(prefix1) or rel_path.startswith(prefix2):
                rel_path = rel_path[len(last) + 1:]

        try:
            filepath = join_path(abs_base, path) or ""
        except PermissionError:
            self.status_code = 403
            self._content = b"403 Forbidden"
            self.headers['Content-Type'] = 'text/plain'
            return 0, self._content

        if os.path.isdir(filepath):
            filepath = os.path.join(filepath, 'index.html')

        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            self.status_code = 404
            self._content = b"404 Not Found"
            self.headers['Content-Type'] = 'text/plain'
            return 0, self._content

        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            self._content = content
            c_len = self.prepare_content_length(self._content)
            return c_len, self._content

        except Exception as e:
            self.status_code = 500
            self._content = b"500 Internal Server Error"
            self.headers['Content-Type'] = 'text/plain'
            print("[Response] ERROR reading file:", e)
            return 0, self._content

    def build_response_header(self, request):
        """
        Constructs the HTTP response headers based on the class:`Request <Request>
        and internal attributes.

        :params request (class:`Request <Request>`): incoming request object.

        :rtypes bytes: encoded HTTP response header.
        """
        reqhdr = getattr(request, "headers", {}) or {}
        rsphdr = self.headers

        status_code = self.status_code or 200
        status_map = {
            200: "OK",
            201: "Created",
            204: "No Content",
            301: "Moved Permanently",
            302: "Found",
            303: "See Other",
            304: "Not Modified",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            500: "Internal Server Error",
        }
        self.reason = status_map.get(status_code, "OK")

        if status_code == 204:
            fmt_header = f"HTTP/1.1 {status_code} {self.reason}\r\n"
            fmt_header += "Server: WeApRous/0.1\r\n"
            fmt_header += "Date: {}\r\n".format(
                datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
            )
            fmt_header += "Connection: close\r\n"
            for k, v in self.headers.items():
                if k.lower().startswith("access-control"):
                    fmt_header += f"{k}: {v}\r\n"
            fmt_header += "\r\n"
            return fmt_header.encode("utf-8")
        #Build dynamic headers
        headers = {
                "Accept": "{}".format(reqhdr.get("Accept", "application/json")),
                "Accept-Language": "{}".format(reqhdr.get("Accept-Language", "en-US,en;q=0.9")),
                # "Authorization": "{}".format(reqhdr.get("Authorization", reqhdr.get("Authorization", "Basic <credentials>"))),
                "Server": "WeApRous/0.1",
                "Date": "{}".format(datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")),
                "Content-Type": "{}".format(rsphdr.get('Content-Type', 'text/html')),
                "Content-Length": "{}".format(len(self._content)),
#                "Cookie": "{}".format(reqhdr.get("Cookie", "sessionid=xyz789")), #dummy cooki
                # "Max-Forward": "10",
                # "Pragma": "no-cache",
                "Connection": "close",
                # "Proxy-Authorization": "Basic dXNlcjpwYXNz",  # example base64
                # "Warning": "199 Miscellaneous warning",
                "User-Agent": "{}".format(reqhdr.get("User-Agent", "Chrome/123.0.0.0")),
                "Cache-Control": "no-cache",
            }
        
        # Header text alignment
        #
        #  TODO: implement the header building to create formated
        #        header from the provied headers
        fmt_header = "HTTP/1.1 {} {}\r\n".format(status_code, self.reason)

        merged = headers.copy()
        for k, v in rsphdr.items():
            merged[k] = v

        printed = set()
        for key, value in merged.items():
            key_lower = key.lower()
            if key_lower in printed:
                continue
            printed.add(key_lower)
            fmt_header += "{:<25} {}\r\n".format(key + ":", value)

        if hasattr(self, 'cookies') and self.cookies:
            for name, value in self.cookies.items():
                fmt_header += f"Set-Cookie: {name}={value}\r\n"

        fmt_header += "\r\n"
        #
        #
        # TODO prepare the request authentication
        #
    
        # self.auth = None 
        # if "Authorization" in reqhdr:
        #     auth_header = reqhdr["Authorization"]
        #     if auth_header.startswith("Basic "):
        #         import base64
        #         try:
        #             encoded_creds = auth_header.split(" ", 1)[1]
        #             decoded_creds = base64.b64decode(encoded_creds).decode('utf-8')
        #             username, password = decoded_creds.split(":", 1)
        #             self.auth = {"username": username, "password": password, "method": "Basic"}
        #         except Exception:
        #             self.auth = None 
        #     else:
        #         self.auth = {"method": auth_header.split(" ", 1)[0]}

        return str(fmt_header).encode('utf-8')

    def build_notfound(self):
        """
        Constructs a standard 404 Not Found HTTP response.

        :rtype bytes: Encoded 404 response.
        """

        return (
                "HTTP/1.1 404 Not Found\r\n"
                "Accept-Ranges: bytes\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: 13\r\n"
                "Cache-Control: max-age=86000\r\n"
                "Connection: close\r\n"
                "\r\n"
                "404 Not Found"
            ).encode('utf-8')

    def prepare_content_length(self, body):
        """Ensure Content-Length header matches the provided body bytes."""
        try:
            length = len(body) if body is not None else 0
        except Exception:
            length = 0
        self.headers['Content-Length'] = str(length)
        return

    def build_response(self, request):
        """
        Builds a full HTTP response including headers and content based on the request.

        :params request (class:`Request <Request>`): incoming request object.

        :rtype bytes: complete HTTP response using prepared headers and content.
        """
        import json
        self.request = request

        if request.method == "OPTIONS":
            header_origin = request.headers.get("Origin", "")
            allow_origin = header_origin if header_origin else "*"

            allow_credentials = allow_origin != "*"

            print(f"[Response] Handling CORS preflight for {request.path} | Origin={header_origin} | AllowCred={allow_credentials}")

            allow_cred_header = "Access-Control-Allow-Credentials: true\r\n" if allow_credentials else ""

            self.headers = (
                "HTTP/1.1 204 No Content\r\n"
                "Server: WeApRous/0.1\r\n"
                "Date: {}\r\n"
                f"Access-Control-Allow-Origin: {allow_origin}\r\n"
                f"{allow_cred_header}"
                "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
                "Access-Control-Allow-Headers: Content-Type, Cookie, Authorization\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).format(datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"))

            return self.headers.encode("utf-8")
        

        if self._content not in (False, None) and self.status_code is not None:
            self.prepare_content_length(self._content)
            self.headers = self.build_response_header(request)
            return self.headers + (self._content if isinstance(self._content, (bytes, bytearray)) else str(self._content).encode('utf-8'))
            
        mime_type = self.get_mime_type(request)
        path = request.path

        print("[Response] {} path {} mime_type {}".format(request.method, request.path, mime_type))

        base_dir = ""

        # TODO: add support objects
        #
        if mime_type:
            base_dir = self.prepare_content_type(mime_type)
        else:
            return self.build_notfound()
        
        if base_dir is None:
            return json.dumps(self.headers).encode("utf-8") + (self._content if isinstance(self._content, (bytes, bytearray)) else str(self._content).encode('utf-8'))

        c_len, self._content = self.build_content(path, base_dir)
        self.headers = self.build_response_header(request)

        if c_len == 0 or self._content == b"404 Not Found":
            return self.build_notfound()
        
        return self.headers + self._content
