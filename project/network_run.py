from mininet.log import setLogLevel
import os
import json

setLogLevel('info')

from project.dragonfly import topology
# from mininet.cli import CLI #import during CLI testing
from project.auto_traffic import keepalive, fdb_refresh_loop
import time
import threading

net = None

try:
    net = topology()
    net.start()

    print("\n[!] Configuring switches...")

    for sw in net.switches:
        sw.cmd(f'ovs-vsctl set-fail-mode {sw.name} standalone')
        sw.cmd(f'ovs-vsctl set Bridge {sw.name} stp_enable=true')

    print("\n[!] Waiting 30s for STP to converge...")
    time.sleep(30)

    print("\nNetwork Established ! Go ahead.\n")

    #CLI(net) #testing purpose

    # ── Start fdb refresh thread for g0_s1 ──
    fbd_refresh_thread = threading.Thread(target=fdb_refresh_loop, 
                                          args=('g0_s1', 1), 
                                          daemon=True)
    fbd_refresh_thread.start()

    # ── Generate traffic Thread ──
    ka_thread = threading.Thread(target=keepalive, 
                                 args=(net,), 
                                 daemon=True)
    ka_thread.start()

    running = True
    try:
        while running:  # main thread program stops (even if other threads are running)
            time.sleep(5)
            # Show live fdb state every 30s
    except KeyboardInterrupt:
        running = False
        print("\n[STOP] Shutting down...")
        net.stop()

except Exception as e:
    print(f"Error: {e}")