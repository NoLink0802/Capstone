#!/usr/bin/env python3
#Test USB / network / HDMI port enumeration. Run: python3 test_ports.py
#DYNAMIC cause might change on each run since bumping HDMI cabe may change  speed and duplex
#Need to figure out what to do with those dynamic values and how much they change

import os

def get_usb_devices() -> dict:
    devices = {}
    for entry in sorted(os.listdir("/sys/bus/usb/devices")):
        dev = f"/sys/bus/usb/devices/{entry}"
        try:
            vendor = open(f"{dev}/idVendor").read().strip()
            product = open(f"{dev}/idProduct").read().strip()
        except OSError:
            continue
        name = []
        for attr in ("manufacturer", "product", "serial"):
            try:
                name.append(open(f"{dev}/{attr}").read().strip())
            except OSError:
                pass
        devices[f"{vendor}:{product}"] = " ".join(name)
    return devices

def get_network_ports() -> dict:
    ports = {}
    for iface in sorted(os.listdir("/sys/class/net")):
        if iface == "lo":
            continue
        info = {}
        for attr in ("address", "carrier", "speed", "duplex"):
            try:
                info[attr] = open(f"/sys/class/net/{iface}/{attr}").read().strip()
            except OSError:
                pass
        ports[iface] = info
    return ports

def get_hdmi_ports() -> dict:
    ports = {}
    if os.path.isdir("/sys/class/drm"):
        for entry in sorted(os.listdir("/sys/class/drm")):
            if "HDMI" in entry:
                try:
                    ports[entry] = open(f"/sys/class/drm/{entry}/status").read().strip()
                except OSError:
                    pass
    return ports

if __name__ == "__main__":
    print("USB devices:")
    for a, b in get_usb_devices().items():
        print(f"  {a}  {b}")

    print("\nNetwork ports: ")
    for iface, info in get_network_ports().items():
        print(f"  {iface}")
        for attr, val in info.items():
            tag = "STATIC " if attr == "address" else "dynamic"
            print(f"    {tag} {attr:<8} {val}")

    print("\nHDMI:")

    for name, status in get_hdmi_ports().items():
        print(f"  STATIC  {name}\n    dynamic status   {status}")