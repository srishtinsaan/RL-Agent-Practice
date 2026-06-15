import time
import subprocess
import re


def run_cmd(cmd):
    """Run shell command"""
    result = subprocess.check_output(cmd, shell=True, text=True)
    return result.strip()


def get_mac_table_entries(sw):

    try:
        output = run_cmd(f"ovs-appctl fdb/show {sw}")

        mac_entries = []

        for line in output.splitlines():

            # Example:
            # port VLAN MAC                 Age
            # 1    1     00:00:00:00:00:01 12

            match = re.search(
                r"(\d+)\s+(\d+)\s+([0-9a-f:]{17})\s+(\d+)",
                line,
                re.IGNORECASE
            )

            if match:

                port = match.group(1)
                vlan = match.group(2)
                mac = match.group(3)
                age = int(match.group(4))

                mac_entries.append({
                    "vlan": vlan,
                    "mac": mac,
                    "port": port,
                    "age": age
                })

        return mac_entries

    except Exception as e:
        print(f"[ERROR] MAC table fetch failed: {e}")
        return []
    

try:
    while True:
        entries = get_mac_table_entries("g0_s1")

        print("\033c") #reset terminal everysecond 
        print("RL MAC TABLE VIEW")
        print("-" * 70)

        if not entries:
            print("Entries : 0")
            time.sleep(1)
            continue

        print(f"Entries : {len(entries)}")

        oldest = max(entries, key=lambda x: int(x.get("age", 0)))

        for e in entries:
            marker = ""
            if e.get("mac") == oldest.get("mac"):
                marker = " <-- WILL BE EVICTED"

            print(
                f"Port {e.get('port')} | "
                f"{e.get('mac')} | "
                f"Age {e.get('age')}s"
                f"{marker}"
            )

        time.sleep(1)

    
except KeyboardInterrupt:
    print("\nStopped cleanly.")