#!/usr/bin/env python3
import subprocess
import json
import argparse
import time

CONFLICT_PROCESSES = [
    "NetworkManager",
    "wpa_supplicant",
    "avahi-daemon",
    "dhclient"
]

def print_banner():
    print("\n[ WIRELESS CTRL ⚙️ HACKERSOUP ]\n")

def list_interfaces():
    result = subprocess.run(["iwconfig"], capture_output=True, text=True).stdout
    interfaces = []
    for line in result.splitlines():
        if "IEEE 802.11" in line:
            iface = line.split()[0]
            interfaces.append(iface)
    return interfaces

def set_monitor_mode(interface):
    subprocess.run(["ip", "link", "set", interface, "down"])
    subprocess.run(["iw", interface, "set", "monitor", "control"])
    subprocess.run(["ip", "link", "set", interface, "up"])

def set_managed_mode(interface):
    subprocess.run(["ip", "link", "set", interface, "down"])
    subprocess.run(["iw", interface, "set", "type", "managed"])
    subprocess.run(["ip", "link", "set", interface, "up"])

def get_mode(interface):
    result = subprocess.run(["iwconfig", interface], capture_output=True, text=True).stdout
    if "Mode:Monitor" in result:
        return "monitor"
    elif "Mode:Managed" in result:
        return "managed"
    else:
        return "unknown"

def output_json(interface):
    mode = get_mode(interface)
    print(json.dumps({
        "interface": interface,
        "mode": mode
    }, indent=2))

def check_conflicts():
    conflicts = []
    for proc in CONFLICT_PROCESSES:
        result = subprocess.run(["pgrep", proc], stdout=subprocess.DEVNULL)
        if result.returncode == 0:
            conflicts.append(proc)
    return conflicts

def kill_conflicts():
    killed = []
    for proc in CONFLICT_PROCESSES:
        result = subprocess.run(["systemctl", "stop", proc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        killed.append(proc)
    return killed

def monitor_scan(interface):
    print(f"📡 Setting {interface} to monitor mode and launching airodump-ng...\n")
    set_monitor_mode(interface)
    time.sleep(2)
    try:
        subprocess.run(["airodump-ng", interface])
    except KeyboardInterrupt:
        print("\n⛔ Scan stopped by user.")
    finally:
        set_managed_mode(interface)
        print(f"\n✅ Restored {interface} to managed mode.")

# === MAIN ===
if __name__ == "__main__":
    print_banner()

    parser = argparse.ArgumentParser(description="Hackersoup Wireless Controller")
    parser.add_argument("--list", action="store_true", help="List wireless interfaces")
    parser.add_argument("--monitor", metavar="iface", help="Set interface to monitor mode")
    parser.add_argument("--managed", metavar="iface", help="Set interface to managed mode")
    parser.add_argument("--status", metavar="iface", help="Print JSON status of interface")
    parser.add_argument("--check", action="store_true", help="Check for conflicting processes")
    parser.add_argument("--kill", action="store_true", help="Stop conflicting processes")
    parser.add_argument("--monitor-scan", metavar="iface", help="Set monitor mode and scan with airodump-ng")

    args = parser.parse_args()

    if args.list:
        interfaces = list_interfaces()
        print(json.dumps({"interfaces": interfaces}, indent=2))
    elif args.monitor:
        set_monitor_mode(args.monitor)
        output_json(args.monitor)
    elif args.managed:
        set_managed_mode(args.managed)
        output_json(args.managed)
    elif args.status:
        output_json(args.status)
    elif args.check:
        conflicts = check_conflicts()
        if conflicts:
            print("⚠️ Conflicting processes detected:")
            print(json.dumps({"conflicts": conflicts}, indent=2))
        else:
            print("✅ No conflicting processes detected.")
    elif args.kill:
        killed = kill_conflicts()
        print("💀 Stopped conflicting processes:")
        print(json.dumps({"killed": killed}, indent=2))
    elif args.monitor_scan:
        monitor_scan(args.monitor_scan)
    else:
        parser.print_help()
