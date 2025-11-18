#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#

"""
start_sampleapp
~~~~~~~~~~~~~~~~~

This module provides a sample RESTful web application using the WeApRous framework.

It defines basic route handlers and launches a TCP-based backend server to serve
HTTP requests. The application includes a login endpoint and a greeting endpoint,
and can be configured via command-line arguments.
"""

import argparse
import json
import sqlite3
import os

from daemon.weaprous import WeApRous
from daemon import Response
from daemon.request import Request

TRACKER_URL = "http://tracker.local:9000"

PORT = 9001
DB_PATH = os.path.join("db", "users.db")
DB_FILE = "db/database.json"

app = WeApRous()

# utils #
def load_db():
    if not os.path.exists(DB_FILE):
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        return {"cookies": []}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"cookies": []}

def save_db(data):
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
###

### Retrieve static files ###
@app.route("/js/main.js", methods=["GET"])
def main_js(req):
    resp = Response(req)
    resp.headers["Content-Type"] = "application/javascript"
    return resp

@app.route("/images/welcome.png")
def img(req):
    resp = Response(req)
    return resp

@app.route("/css/styles.css")
def style(req):
    resp = Response(req)
    return resp

@app.route("/favicon.ico")
def favicon(req):
    resp = Response(req)
    resp.headers['Location'] = '/images/favicon.ico'
    return resp
###

### Task 1: Login ###

@app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
def index(req):
    resp = Response(req)
    cookies = req.cookies or {}
    auth = cookies.get("auth", "")

    if auth != 'true':
        resp.status_code = 401
        resp.content = b"401 Unauthorized"
        return resp
    
    resp.headers["Content-Type"] = "text/html"
    with open("www/index.html", "rb") as f:
        resp.content = f.read()
    return resp

@app.route("/login.html", methods=["GET"])
def login_form(req):
    resp = Response(req)
    with open("www/login.html", "rb") as f:
        resp.content = f.read()
    return resp

@app.route("/login", methods=["POST"])
def login(req):
    resp = Response(req)
    body = req.json or req.form or {}
    try:
        username = body.get("username")
        password = body.get("password")

        print('[POST LOGIN] username: {} and password: {}'.format(username, password))

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()

        if user:
            resp.cookies["auth"] = "true"
            resp.cookies["username"] = username
            
            db = load_db()
            found = False
            for c in db["cookies"]:
                if c["username"] == username:
                    c["cookies"] = {"auth": "true", "username": username}
                    found = True
                    break
            if not found:
                db["cookies"].append({
                    "username": username,
                    "cookies": {"auth": "true", "username": username}
                })
            save_db(db)
            
            resp.redirect(location='/')
            return resp
        else:
            resp.status_code = 401
            resp.headers["Content-Type"] = "application/json"
            resp.content = json.dumps({"status": "error", "message": "Wrong username or password!"}).encode("utf-8")
            return resp

    except Exception as e:
        print("[LOGIN ERROR]", e)
        resp.status_code = 500
        resp.content = b"Internal error"
        return resp

@app.route("/logout", methods=["GET"])
def logout(req):
    resp = Response(req)
    try:
        username_to_logout = req.cookies.get("username")
        
        if username_to_logout:
            db = load_db()
            original_count = len(db["cookies"])
            db["cookies"] = [c for c in db["cookies"] if c.get("username") != username_to_logout]
            if len(db["cookies"]) < original_count:
                save_db(db)
            else:
                print(f"[LOGOUT] Cannot find {username_to_logout} in db.json.")
                
    except Exception as e:
        print(f"[LOGOUT ERROR]: {e}")

    resp.set_cookie("auth", "false", max_age=0)
    resp.set_cookie("username", "", max_age=0)
    
    resp.redirect(location='/login.html')
    return resp

### Task 2: Get list of connected peer and current channel ###

@app.route("/get-list", methods=["GET"])
def get_list(req):
    resp = Response(req)
    if not req.cookies.get("auth") == "true":
        resp.status_code = 401
        resp.content = json.dumps({"status": "error", "message": "Unauthorized"}).encode("utf-8")
        return resp

    user_cookie_header = req.headers.get("Cookie", "")

    tracker_request = Request()
    
    try:
        resp_tracker_raw = tracker_request.send(
            method="GET",
            url=f"{TRACKER_URL}/get-list",
            headers={"Cookie": user_cookie_header},
            useProxy=True 
        )

        if "\r\n\r\n" in resp_tracker_raw:
            header_part, body_part = resp_tracker_raw.split("\r\n\r\n", 1)
        else:
            header_part, body_part = "", ""

        if "HTTP/1.1 200 OK" not in header_part:
          raise Exception("Tracker returned an error")

        resp.status_code = 200
        resp.headers["Content-Type"] = "application/json"
        resp.content = body_part.encode("utf-8")
        return resp

    except Exception as e:
        print(f"[GET-LIST ERROR] Error when get-list from Tracker: {e}")
        resp.status_code = 502 
        resp.content = json.dumps({"status": "error", "message": "Can't connect to Tracker"}).encode("utf-8")
        return resp

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='WeApRous', description='Web Dashboard')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)

    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    app.prepare_address(ip, port)
    app.run()