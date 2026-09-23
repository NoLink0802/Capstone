#!/usr/bin/env python3
#Test the default gateway. Run: python3 test_gateway.py
#

import socket, struct, subprocess

def get_default_gateway() -> dict:
    gateways = {}
    with open("/proc/net/route") as f:
        next(f)
        for line in f:
            iface, dest, gw, flags = line.split()[:4]
            if dest == "00000000" and int(flags, 16) & 0x2:
                gateways[iface] = socket.inet_ntoa(struct.pack("<L", int(gw, 16)))
    return gateways

if __name__ == "__main__":
    print( get_default_gateway())
    print("ip route:", subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True).stdout.strip())