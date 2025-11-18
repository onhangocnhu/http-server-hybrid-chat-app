import json, time, sys, argparse

from daemon.weaprous import WeApRous
from daemon.request import Request
from daemon.response import Response, _json
from daemon.utils import add_cors, auth_check

TRACKER_URL = "http://tracker.local:9000"
DB_FILE = "db/database.json"

app = WeApRous()

LOCAL_ACTIVE_PEERS = {} 
CONNECTED_LIST = []
MESSAGES = []           
MSG_ID_COUNTER = 0

class Peer:
    def __init__(self, username, peer_ip, peer_port):
        self.username = username
        self.peer_ip = peer_ip
        self.peer_id = f"peer-{username}"
        self.peer_port = peer_port
        self.cookie = self._load_cookie()
        self.cookie_header = "; ".join(f"{k}={v}" for k, v in self.cookie.items())
        
        if not self.cookie.get("auth") == "true":
            raise Exception(f"Cannot find cookie authentication for '{username}'. Please login first.")

    def _load_cookie(self):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
            for c in db["cookies"]:
                if c["username"] == self.username:
                    return c["cookies"]
        except Exception as e:
            print(f"[Cookie] Error when read file db/database.json: {e}")
        return {}

    def register_to_server(self):
        print(f"\n[Peer Client] submit-info: {self.peer_id} (IP: {self.peer_ip}, Port: {self.peer_port}) to Tracker...")
        data = {
            "ip": self.peer_ip, 
            "port": self.peer_port,
        }
        headers = {"Cookie": self.cookie_header}
        req = Request()

        try:
            resp_str = req.send(
                method="POST",
                url=f"{TRACKER_URL}/submit-info",
                json_data=data,
                headers=headers,
                useProxy=False
            )
            
            if "HTTP/1.1 200 OK" in resp_str:
                print("[Peer Client] submit-info: Submit info to Server Tracker successfully")
                return True, None
            else:
                print(f"[Peer Client] submit-info error: {resp_str.splitlines()[0]}")
                return False, resp_str
        except Exception as e:
            print(f"[Peer Client] submit-info error: Error when connect to Server Tracker: {e}")
            return False, str(e)

@app.route("/submit-info", methods=["GET"])
def serve_submit(req):
    resp = Response(req)
    with open("www/chat.html", "rb") as f:
        resp.content = f.read()
        resp.headers["Content-Type"] = "text/html"
    return resp

@app.route("/chat.html", methods=["GET"])
def chat(req):
    resp = Response(req)
    try:
        with open("www/chat.html", "rb") as f: resp.content = f.read()
        resp.headers["Content-Type"] = "text/html"
    except FileNotFoundError:
        resp.status_code = 404
        resp.content = b"File not found: www/chat.html. (Chay 'python peer_backend.py --username user1 --port 9005')"
    return resp

@app.route("/chat_channel.html", methods=["GET"])
def chat_channel(req):
    resp = Response(req)
    if not auth_check(app.peer_client.username, req): return _json({"error": "Unauthorized"}, 401)
    with open("www/chat_channel.html", "rb") as f: resp.content = f.read()
    resp.headers["Content-Type"] = "text/html"
    return resp

@app.route("/chat_room.html", methods=["GET"])
def chat_room(req):
    resp = Response(req)
    if not auth_check(app.peer_client.username, req): return _json({"error": "Unauthorized"}, 401)
    with open("www/chat_room.html", "rb") as f: resp.content = f.read()
    resp.headers["Content-Type"] = "text/html"
    return resp
    
@app.route("/current_channel.html", methods=["GET"])
def current_channel(req):
    resp = Response(req)
    if not auth_check(app.peer_client.username, req): return _json({"error": "Unauthorized"}, 401)
    with open("www/current_channel.html", "rb") as f: resp.content = f.read()
    resp.headers["Content-Type"] = "text/html"
    return resp

@app.route("/js/submit-info.js", methods=["GET"])
def js_submit(req):
    resp = Response(req)
    with open("static/js/submit-info.js", "rb") as f: resp.content = f.read()
    resp.headers["Content-Type"] = "application/javascript"
    return resp

@app.route("/js/chat_channel.js", methods=["GET"])
def js_channel(req):
    resp = Response(req)
    with open("static/js/chat_channel.js", "rb") as f: resp.content = f.read()
    resp.headers["Content-Type"] = "application/javascript"
    return resp

@app.route("/js/chat_room.js", methods=["GET"])
def js_room(req):
    resp = Response(req)
    with open("static/js/chat_room.js", "rb") as f: resp.content = f.read()
    resp.headers["Content-Type"] = "application/javascript"
    return resp
    
@app.route("/js/current_channel.js", methods=["GET"])
def js_current(req):
    resp = Response(req)
    with open("static/js/current_channel.js", "rb") as f: resp.content = f.read()
    resp.headers["Content-Type"] = "application/javascript"
    return resp

@app.route("/favicon.ico")
def style(req):
    resp = Response(req)
    resp.headers['Location'] = '/images/favicon.ico'
    return resp

@app.route("/css/styles.css")
def style(req):
    resp = Response(req)
    return resp

@app.route("/submit-info", methods=["POST"])
def submit_info(req):
    resp = Response(req)
    peer = app.peer_client
    
    success, error_response = peer.register_to_server()
    
    if success:
        resp.status_code = 200
        resp.content = json.dumps({
            "status": "ok",
            "message": "Register successful!",
            "owner": peer.username, 
            "ip": peer.peer_ip, 
            "port": peer.peer_port
        }).encode("utf-8")
        resp.cookies["auth"] = peer.cookie.get("auth")
        resp.cookies["username"] = peer.cookie.get("username")
        return resp
    else:
        if error_response and "Already submit" in error_response:
            print("[Peer Client] submit-info: Peer has been submitted.")
            resp.status_code = 409 
            resp.content = json.dumps({
                "status": "error", 
                "message": "You are already registered. Redirecting...",
                "owner": peer.username, 
                "ip": peer.peer_ip, 
                "port": peer.peer_port
            }).encode("utf-8")
            resp.cookies["auth"] = peer.cookie.get("auth")
            resp.cookies["username"] = peer.cookie.get("username")
            return resp
        else:
            resp.status_code = 500
            resp.content = json.dumps({
                "status": "error", 
                "message": f"Failed to register: {error_response}"
            }).encode("utf-8")
            return resp

@app.route("/get-list", methods=["GET"])
def get_list(req):
    if not auth_check(app.peer_client.username, req): return _json({"error": "Unauthorized"}, 401)
    
    peer = app.peer_client
    print("\n[Peer Client] get-list: forwarding to Tracker...")
    
    try:
        req_to_tracker = Request()
        resp_tracker_raw = req_to_tracker.send(
            method="GET",
            url=f"{TRACKER_URL}/get-list",
            headers={"Cookie": peer.cookie_header}, 
            useProxy=False
        )
        
        if "\r\n\r\n" in resp_tracker_raw:
            header_part, body_part = resp_tracker_raw.split("\r\n\r\n", 1)
        else: header_part, body_part = "", ""

        if "HTTP/1.1 200 OK" not in header_part:
            raise Exception(f"Tracker error: {header_part.splitlines()[0]}")

        global LOCAL_ACTIVE_PEERS
        LOCAL_ACTIVE_PEERS = json.loads(body_part).get("active_peers", {})
        
        resp = Response(req)
        resp.status_code = 200
        resp.headers["Content-Type"] = "application/json"
        resp.content = body_part.encode("utf-8")
        return add_cors(resp)

    except Exception as e:
        print(f"[Peer Client] get-list error: {e}")
        resp.status_code = 500
        resp.content = json.dumps({"status": "error", "message": "Can't connect to Tracker"})
        return resp

@app.route("/connect-peer", methods=["POST"])
def connect_peer(req):
    if not auth_check(app.peer_client.username, req):
        return _json({"error": "Unauthorized"}, 401)
    
    data = req.json or {}
    me = data.get("from")
    target = data.get("to")

    if not LOCAL_ACTIVE_PEERS:
        get_list(req)

    if not me or not target:
        return _json({"status": "error", "message": "Missing from/to"}, 400)

    if target not in LOCAL_ACTIVE_PEERS:
        return _json({"status": "error", "message": "Peer not found"}, 400)

    LOCAL_ACTIVE_PEERS.setdefault(me, {}).setdefault("connected", [])
    LOCAL_ACTIVE_PEERS.setdefault(target, {}).setdefault("connected", [])

    if target not in LOCAL_ACTIVE_PEERS[me]["connected"]:
        LOCAL_ACTIVE_PEERS[me]["connected"].append(target)
    if me not in LOCAL_ACTIVE_PEERS[target]["connected"]:
        LOCAL_ACTIVE_PEERS[target]["connected"].append(me)

    print(f"\n[Peer Client] connect-peer: {me} <-> {target}")
    return _json({"status": "ok", "message": f"{me} connected to {target}"})


@app.route("/send-peer", methods=["POST"])
def send_peer(req):
    if not auth_check(app.peer_client.username, req): return _json({"error": "Unauthorized"}, 401)
    
    peer = app.peer_client
    data = req.json or {}
    sender = data.get("from")
    target = data.get("to")  
    message = data.get("message")
    ts = time.strftime("%H:%M:%S")

    if sender != peer.peer_id:
        return _json({"status": "error", "message": "Sender ID mismatch"}, 400)

    tgt_info = LOCAL_ACTIVE_PEERS.get(target)
    if not tgt_info:
        print(f"[Peer Client] send-peer error: Cannot find {target}")
        return _json({"status": "error", "message": f"Target {target} not found."}, 404)

    target_ip = tgt_info["ip"]
    target_port = tgt_info["port"]
    target_url = f"http://{target_ip}:{target_port}/receive"
    
    global MSG_ID_COUNTER
    MSG_ID_COUNTER += 1
    MESSAGES.append({
        "id": MSG_ID_COUNTER, 
        "from": sender, "to": target, 
        "message": message, "ts": ts
    })
    
    print(f"\n[Peer Client] send-peer {sender} -> {target_url}...")
    try:
        p2p_request = Request()
        resp_recv = p2p_request.send(
            method="POST",
            url=target_url,
            headers={"Content-Type": "application/json"},
            json_data={"from": sender, "to": target, "message": message, "ts": ts},
            useProxy=False
        )
        print(f"[Peer Client] send-peer result: {resp_recv.splitlines()[0]}")
    except Exception as e:
        print(f"[Peer Client] send-peer error: {e}")
        return _json({"status": "error", "message": str(e)}, 500)
    
    return _json({"status": "ok", "message": "sent"})

@app.route("/broadcast-peer", methods=["POST"])
def broadcast_peer(req):
    if not auth_check(app.peer_client.username, req): 
        return _json({"error": "Unauthorized"}, 401)

    peer = app.peer_client
    data = req.json or {}
    sender = data.get("from")
    message = data.get("message")
    ts = time.strftime("%H:%M:%S")

    if sender != peer.peer_id:
        return _json({"status": "error", "message": "Sender ID mismatch"}, 400)

    if not LOCAL_ACTIVE_PEERS:
        return _json({"status": "error", "message": "No peers to broadcast to (please Get List first)"}, 404)

    peer_name = sender.split("peer-")[-1]
    global MSG_ID_COUNTER
    MSG_ID_COUNTER += 1
    MESSAGES.append({
        "id": MSG_ID_COUNTER,
        "from": sender,
        "to": "ALL",
        "message": message,
        "ts": ts
    })
    resp_connected = get_connected(req)

    data = json.loads(resp_connected.content.decode("utf-8"))
    connected_peers = data.get("connected_peers", [])

    for peer in connected_peers:
        if peer['owner'] == peer_name:
            continue 

        try:
            peer_owner = peer['owner']
            peer_url = f"http://{app.peer_client.peer_ip}:{app.peer_client.peer_port}/send-peer"

            Request().send(
                method="POST",
                url=peer_url,
                headers=req.headers,
                json_data={
                    "from": sender,
                    "to": peer['id'],
                    "message": message,
                    "ts": ts
                },
                useProxy=False
            )
            print(f"\n[Peer Client] broadcast-peer: {app.peer_client.peer_id} -> ALL")
        except Exception as e:
            print(f"[Peer Client] broadcast-peer error: {e}")

    return _json({"status": "ok", "message": "Broadcast finished"})

@app.route("/get-messages", methods=["GET"])
def get_messages(req):
    if not auth_check(app.peer_client.username, req): 
        return _json({"error": "Unauthorized"}, 401)
        
    print(f"\n[Peer Client] get-messages: Return {len(MESSAGES)} messages.") 
    
    return _json({"messages": MESSAGES})

@app.route("/get-connected", methods=["GET"])
def get_connected(req):
    if not auth_check(app.peer_client.username, req):
        return _json({"error": "Unauthorized"}, 401)

    my_peer_id = app.peer_client.peer_id

    if not LOCAL_ACTIVE_PEERS:
        get_list(req)

    connected_peers = []

    my_info = LOCAL_ACTIVE_PEERS.get(my_peer_id, {})
    my_connected = set(my_info.get("connected", []))

    for pid, info in LOCAL_ACTIVE_PEERS.items():
        if pid == my_peer_id:
            continue

        other_connected = info.get("connected", [])
        if pid in my_connected or my_peer_id in other_connected:
            connected_peers.append({
                "id": pid,
                "ip": info.get("ip"),
                "port": info.get("port"),
                "owner": info.get("owner")
            })

    return _json({"connected_peers": connected_peers})


@app.route("/receive", methods=["OPTIONS"])
def receive_options(req):
    resp = Response(req)
    resp.status_code = 204
    return add_cors(resp)

@app.route("/receive", methods=["POST"])
def receive(req):
    peer = app.peer_client
    resp = Response(req)
    data = req.json or {}
    sender = data.get("from")
    message = data.get("message")
    
    print(f"\n[Peer Client] receive message: {sender} -> Me ({peer.peer_id}): {message}")

    global MSG_ID_COUNTER
    MSG_ID_COUNTER += 1
    MESSAGES.append({
        "id": MSG_ID_COUNTER, 
        "from": sender, 
        "to": peer.peer_id,
        "message": data.get("message"), 
        "ts": data.get("ts", time.strftime("%H:%M:%S"))
    })
    
    return add_cors(_json({"status": "ok", "message": "received"}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='PeerBackend', 
        description='Peer P2P Backend'
    )
    parser.add_argument(
        '--peer-ip', 
        default="127.0.0.1",
        required=True, 
        help="Register IP address"
    )
    parser.add_argument(
        '--peer-username', 
        required=True, 
        help="Logged in username"
    )
    parser.add_argument(
        '--peer-port', 
        type=int, 
        required=True, 
        help="Port number of peer"
    )
    
    args = parser.parse_args()
    
    ip = args.peer_ip
    username = args.peer_username
    port = args.peer_port

    try:
        peer = Peer(username, ip, port)
        app.peer_client = peer
        app.prepare_address(ip, port)
        print(f"[Peer Client] Running Peer Backend for {peer.peer_id}")
        print(f"[Peer Client] Running at: http://{ip}:{port}/submit-info")
        
        app.run()
        
    except Exception as e:
        print(f"\n[Peer Client] error {e}")
        sys.exit(1)