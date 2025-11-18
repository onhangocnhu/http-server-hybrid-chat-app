#!/usr/bin/env python3
"""
Update proxy.conf with the actual LAN IP address.
Run this on the server machine before starting services.
"""
import os
import sys

from get_lan_ip import get_lan_ip

def update_proxy_conf():
    """Update proxy.conf with actual LAN IP"""
    lan_ip = get_lan_ip()
    
    config_template = f'''host "tracker.local" {{
    proxy_pass http://{lan_ip}:9000;
}}

host "app.local" {{
    proxy_set_header Host $host;

    proxy_pass http://{lan_ip}:9001;
    proxy_pass http://{lan_ip}:9002;

    dist_policy round-robin
}}
'''
    
    config_path = os.path.join('config', 'proxy.conf')
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_template)
        print(f"[OK] Updated {config_path} with IP: {lan_ip}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update proxy.conf: {e}")
        return False

def show_hosts_instructions():
    """Show instructions for updating hosts file"""
    lan_ip = get_lan_ip()
    print("\n" + "="*60)
    print("IMPORTANT: Update your hosts file with:")
    print("="*60)
    print(f"{lan_ip} tracker.local")
    print(f"{lan_ip} app.local")
    print("\nOn Windows: C:\\Windows\\System32\\drivers\\etc\\hosts")
    print("On Linux/Mac: /etc/hosts")
    print("="*60 + "\n")

if __name__ == "__main__":
    print("Updating proxy.conf with LAN IP...")
    if update_proxy_conf():
        show_hosts_instructions()
        sys.exit(0)
    else:
        sys.exit(1)
