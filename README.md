# WeApRous

***WeApRous*** is a lightweight educational web framework designed for Computer Network coursework in *VNU-HCM Ho Chi Minh City University of Technology (HCMUT)*. It provides a fully custom HTTP stack, a minimal web server, routing, cookie/session handling, and a hybrid P2P chat module. 

The entire system is implemented without external web frameworks, allowing full control over request parsing, response handling, and network behavior.

## Project Structure

```
weparous/
│
├── config/
│   ├── proxy.conf        # Configuration for proxy
├── daemon/
│   ├── weaprous.py       # WeApRous object to deploy RESTful url web app with routing
│   ├── backend.py        # backend server using Python's socket and threading libraries
│   ├── proxy.py          # a simple proxy server using Python's socket and threading libraries
│   ├── request.py        # Custom Request parser (cookies, headers, body)
│   ├── response.py       # Response builder with MIME handling
│   ├── httpadapter.py    # HTTP handler for all incoming requests
│   ├── dictionary.py     # Case-insensitive dict for headers
│   ├── utils.py          # Helper utilities
├── start_backend.py  # Backend for tracker server
├── start_proxy.py    # Reverse-proxy with round-robin load balancing
├── start_peer.py     # Standalone P2P backend for each peer
├── start_sampleapp.py # Backend that serves UI login, dashboard pages
├── www/
│   ├── login.html
│   ├── index.html
│   ├── chat.html
│   ├── chat_channel.html
│   ├── current_channel.html
│   ├── chat_room.html
├── static/
│   ├── js/
│   │   ├── main.js
│   │   ├── submit-info.js
│   │   ├── chat_channel.js
│   │   ├── current_channel.js
│   │   ├── chat_room.js
│   ├── css/
│   │   └── styles.css
│   ├── images/
│   │   └── # images used for the UI
├── db/
│   ├── database.json
│   ├── init_db.py
│   ├── users.db
└── README.md
```

## How to Run
**1. Start the Tracker, UI Backends, and Proxy**
- A batch script is provided to launch everything in separate terminals ``run_server.bat``.

This script launches:
- Tracker server (port 9000)
- UI backend 1 (port 9001)
- UI backend 2 (port 9002)
- Reverse proxy (port 8080)

These services can also be started manually:

```bat
start "Tracker" cmd /k python start_backend.py --server-ip 0.0.0.0 --server-port 9000
timeout /t 2 /nobreak >nul

start "Backend UI 1" cmd /k python start_sampleapp.py --server-ip 0.0.0.0 --server-port 9001
timeout /t 1 /nobreak >nul

start "Backend UI 2" cmd /k python start_sampleapp.py --server-ip 0.0.0.0 --server-port 9002
timeout /t 1 /nobreak >nul

start "Proxy" cmd /k python start_proxy.py --server-ip 0.0.0.0 --server-port 8080
```

***LAN Mode (Multiple Computers)***

``run_server.bat`` automatically configures the system for multi-machine use over the same Wi-Fi/LAN network.

The script:
- Detects the server’s LAN IP
- Updates ``proxy.conf`` accordingly
- Prints instructions for connecting from other devices
- Shows the required Windows hosts entries:
```lua
<LAN_IP> tracker.local
<LAN_IP> app.local
```

Other machines can access the system via:
```arduino
http://<LAN_IP>:8080
```
Port ``8080`` is used to demonstrate the reverse proxy with round-robin routing.

**2. Access the Application**

Open your browser:
```arduino
http://app.local:8080
```

With the ``app.local`` registered ip and port is:
```
{your_tracker_ip}:{your_tracker_port}
```

*(Ensure your hosts file maps ``app.local`` to the LAN IP of the server.)*

From the UI you can: log in,
view active peers.

**3. Initiate your Peer instances**

After logging in, each user must run their own peer backend:

```shell
python start_peer.py --peer-ip {your_ip} --peer-username {your_username} --peer-port {your_port}
```

- Example for peer1:
```bat
python start_peer.py --peer-ip 192.168.1.3 --peer-username peer1 --peer-port 9003
```

- Example for peer2:

```bat
python start_peer.py --peer-ip 192.168.1.6 --peer-username peer2 --peer-port 9004
```

Each peer operates as an independent backend capable of:
- Registering itself to the tracker
- Connecting to other active peers
- Opening direct chat channels
- Broadcasting messages
- Exchanging P2P messages without going through the tracker

Open the browser, for your Peer, enter ``http://{your_peer_ip}:{your_peer_port}/submit-info`` to continue. 