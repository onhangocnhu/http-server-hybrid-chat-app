#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
start_backend
~~~~~~~~~~~~~~~~~

This module provides a simple entry point for deploying backend server process
using the socket framework. It parses command-line arguments to configure the
server's IP address and port, and then launches the backend server.
"""

import json
import argparse
import time
from daemon import create_backend
from daemon.weaprous import WeApRous
from daemon.response import Response

# Default port number used if none is specified via command-line arguments.
PORT = 9000 
app = WeApRous()

ACTIVE_PEERS = {}

@app.route("/submit-info", methods=["POST"])
def submit_info(req):
    resp = Response(req)
    if not req.cookies.get("auth") == "true":
        resp.status_code = 401
        resp.headers["Content-Type"] = "application/json"
        resp.content = b"401 Unauthorized"
        return resp
    
    data = req.json or {}
    ip = data.get("ip")
    port = str(data.get("port"))
    username = req.cookies.get("username", "")
    peer_id = "peer-{}".format(username)

    print("\n[Server Tracker] submit-info: ip {} and port {}".format(ip, port))

    if not ip or not port:
        resp.status_code = 400
        resp.headers["Content-Type"] = "application/json"
        resp.content = b"Bad Request"
        return resp
    
    for pid, info in ACTIVE_PEERS.items():
        if info.get("owner") == username:
            resp.status_code = 400
            resp.headers["Content-Type"] = "application/json"
            resp.content = b"Already submit"
            return resp
    
    request_add = req
    request_add.json['owner'] = username
    add_list(request_add)

    print(f"[Server Tracker] submit-info: Peer {peer_id} registered.")

    resp.status_code = 200
    resp.headers["Content-Type"] = "application/json"
    resp.content = json.dumps({"ip": ip, "port": port, "owner": username}).encode("utf-8")

    return resp

@app.route("/add-list", methods=["OPTIONS"])
def add_list_options(req):
    resp = Response(req)
    return resp

@app.route("/add-list", methods=["POST"])
def add_list(req):
    resp = Response(req)
    
    origin = req.headers.get("Origin", "*")
    resp.headers["Access-Control-Allow-Origin"] = origin
    resp.headers["Access-Control-Allow-Credentials"] = "true"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    
    data = req.json or {}
    ip = data.get("ip")
    port = str(data.get("port"))
    owner = data.get("owner")
    print("[Server Tracker] add-list: ip is {} and port is {} with owner {}".format(ip, port, owner))

    peer_id = f"peer-{owner}"
    ACTIVE_PEERS[peer_id] = {
        "ip": ip, 
        "port": port, 
        "owner": owner,
        "last_seen": time.time()
    }
    print(f"[Server Tracker] add-list: Added {peer_id} ({ip}:{port}) with {owner}")

    resp.status_code = 200
    resp.headers["Content-Type"] = "application/json"
    resp.content = json.dumps({
        "status": "ok",
        "message": f"{peer_id} ({ip}:{port}) registered"
    }).encode("utf-8")
    return resp

@app.route("/get-list", methods=["GET"])
def get_list(req):
    resp = Response(req)
    user = req.cookies.get("username")
    current_peer_id = f"peer-{user}"

    print(f"\n[Server Tracker] get-list: Request by {current_peer_id}, peers: {list(ACTIVE_PEERS.keys())}")
    resp.status_code = 200
    resp.headers["Content-Type"] = "application/json"
    resp.content = json.dumps({"active_peers": ACTIVE_PEERS}).encode("utf-8")
    return resp

if __name__ == "__main__":
    """
    Entry point for launching the backend server.

    This block parses command-line arguments to determine the server's IP address
    and port. It then calls `create_backend(ip, port)` to start the RESTful
    application server.

    :arg --server-ip (str): IP address to bind the server (default: 127.0.0.1).
    :arg --server-port (int): Port number to bind the server (default: 9000).
    """

    parser = argparse.ArgumentParser(
        prog='Backend',
        description='Start the backend process',
        epilog='Backend daemon for http_daemon application'
    )
    parser.add_argument('--server-ip',
        type=str,
        default='0.0.0.0',
        help='IP address to bind the server. Default is 0.0.0.0'
    )
    parser.add_argument(
        '--server-port',
        type=int,
        default=PORT,
        help='Port number to bind the server. Default is {}.'.format(PORT)
    )

    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    create_backend(ip, port, routes=app.routes)
