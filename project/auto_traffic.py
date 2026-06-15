#from mininet.topo import Topo
#from mininet.net import Mininet
#from mininet.node import Controller
#import threading
#import os
#from mininet.log import setLogLevel

import time
import subprocess
import random
import threading

def fdb_refresh_loop(switch_name, interval=1):
    """
    Continuously dump FDB for RL agent.
    """
    fdb_file = f"/tmp/fdb_{switch_name}.txt"

    while True:
        try:
            result = subprocess.run(
                ["ovs-appctl", "fdb/show", switch_name],
                capture_output=True,
                text=True
            )

            lines = result.stdout.splitlines()
            entries = max(0, len(lines) - 1)

            print(f"[FDB] Entries={entries}")

            with open(fdb_file, "w") as f:
                f.write(result.stdout)

        except Exception as e:
            print(f"[FDB ERROR] {e}")

        time.sleep(interval)

def bootstrap_learning(net):
    """
    One-time startup traffic so switch learns some MACs.
    """
    all_hosts = net.hosts

    print("[BOOTSTRAP] Initial MAC learning")

    for host in all_hosts:

        candidates = [h for h in all_hosts if h != host]

        if not candidates:
            continue

        dst = random.choice(candidates)

        host.cmd(
            f"ping -c 1 {dst.IP()} > /dev/null 2>&1"
        )

    time.sleep(2)

    print("[BOOTSTRAP] Done")

stop_event = threading.Event()
def random_keepalive(net):
    """
    Very light refresh traffic.
    Keeps some MAC entries alive.
    """

    all_hosts = [h for h in net.hosts if h.intf() is not None] 

    count = random.randint(1, max(1, len(all_hosts) // 5) ) #Picks 1 to ~20% of hosts

    hosts = random.sample(all_hosts, min(count, len(all_hosts))) #Random subset of active senders.

    for src in hosts:

        candidates = [h for h in all_hosts if h != src]
        if not candidates:
            continue
        dst = random.choice(candidates)
        src.cmd(f"ping -c 1 {dst.IP()} > /dev/null 2>&1 &")

    print(f"[KEEPALIVE] Refreshed {len(hosts)} hosts")

def start_user_session(net):
    """
    Simulate a temporary user activity session.
    """

    all_hosts = net.hosts

    src = random.choice(all_hosts)

    candidates = [h for h in all_hosts if h != src]

    if not candidates:
        return

    dst = random.choice(candidates)

    duration = random.choice([
        30,
        60,
        120,
        180,
        300
    ])

    interval = random.choice([
        0.5,
        1.0,
        2.0
    ])

    src.cmd(
        f"timeout {duration} "
        f"ping -i {interval} {dst.IP()} "
        f"> /dev/null 2>&1 &"
    )

    print(
        f"[SESSION] "
        f"{src.name} -> {dst.name} "
        f"for {duration}s"
    )

def start_burst(net):
    """
    Simulate a busy period.
    Multiple temporary flows.
    """

    all_hosts = net.hosts

    print("[BURST] Starting burst")

    num_flows = random.randint(
        max(2, len(all_hosts)//4),
        max(3, len(all_hosts)//2)
    )

    for _ in range(num_flows):

        src = random.choice(all_hosts)

        candidates = [
            h for h in all_hosts
            if h != src
        ]

        if not candidates:
            continue

        dst = random.choice(candidates)

        duration = random.randint(
            60,
            180
        )

        src.cmd(f"timeout {duration} ping -i 0.5 {dst.IP()} > /dev/null 2>&1 &")

    print(f"[BURST] {num_flows} flows started")

def keepalive(net):

    print("[TRAFFIC] Event-driven traffic engine started")

    last_burst = time.time()

    while not stop_event.is_set():

        try:
            if random.random() < 0.4:
                random_keepalive(net)

            if random.random() < 0.3:
                start_user_session(net)

            burst_interval = random.randint(300, 600)

            if time.time() - last_burst > burst_interval:
                start_burst(net)
                last_burst = time.time()
        
        except Exception as e:
            if stop_event.is_set():
                break               # ← silent exit on shutdown
            print(f"[WARN] keepalive error: {e}")

        time.sleep(10)
    print("[TRAFFIC] Keepalive stopped cleanly")
                