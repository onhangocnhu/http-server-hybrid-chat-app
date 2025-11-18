#!/usr/bin/env python3
"""
Utility to get the LAN IP address of this machine.
Used for multi-machine setup.
"""
import socket

def get_lan_ip():
    """
    Get the LAN IP address by creating a dummy connection.
    Returns the local IP address on the LAN.
    """
    try:
        # Create a socket and connect to an external address
        # This doesn't actually send data, just determines which interface would be used
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
        return lan_ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    ip = get_lan_ip()
    print(f"LAN IP: {ip}")
