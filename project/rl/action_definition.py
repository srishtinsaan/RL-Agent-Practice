import subprocess
from monitor import get_mac_table_entries
import time


AGING_HIGH       = 600
AGING_LOW        = 60

def run_cmd(cmd):
    try:
        result = subprocess.check_output(cmd, shell=True, text=True)
        return result.strip()
    except subprocess.CalledProcessError as e:
        print("\n[WARN] Command failed")
        print("CMD:", e.cmd)
        print("Return code:", e.returncode)
        print("STDERR:", e.stderr)

        # IMPORTANT: don't crash RL training
        return None

def action_learn_mac(sw):
    pass

def action_evict_entry(sw):
    """Evict only the single stalest MAC entry. Does NOT flush the whole table."""
    try:
        mac_entries = get_mac_table_entries(sw)

        if not mac_entries:
            print(f"  [ACTION] EVICT_ENTRY — table already empty, nothing to evict on {sw}")
            return None

        stalest    = max(mac_entries, key=lambda e: e["age"])
        stale_mac  = stalest["mac"]
        stale_port = stalest["port"]
        stale_age  = stalest["age"]

        print(f"  [ACTION] EVICT_ENTRY — evicting MAC {stale_mac} "
              f"(port {stale_port}, age {stale_age}s) on {sw}")
        
        run_cmd(
            f"ovs-ofctl add-flow {sw} "
            f"priority=100,dl_src={stale_mac},actions=drop"
        )

        time.sleep(2)
        run_cmd(f"ovs-ofctl del-flows {sw} dl_src={stale_mac}")

        print(f"  [ACTION] EVICT_ENTRY — MAC {stale_mac} evicted and rule cleared")
        return stale_mac

    except Exception as e:
        print(f"  [ERROR] EVICT_ENTRY failed: {e}")
        return None

def action_flood(sw):
    # Secure mode so rule takes precedence; idle_timeout=10 auto-expires the rule
    run_cmd(f"ovs-vsctl set-fail-mode {sw} secure")
    run_cmd(f"sudo ovs-ofctl add-flow {sw} cookie=0xDEAD,priority=1,idle_timeout=10,actions=FLOOD")
    print(f"  [ACTION] FLOOD — Temporary flooding rule added (10s idle timeout) on {sw}")

def action_increase_aging(sw):
    """Increase MAC aging timer — entries live longer"""
    try:
        run_cmd(f"ovs-vsctl set Bridge {sw} other_config:mac-aging-time={AGING_HIGH}")
        print(f"  [ACTION] INCREASE_AGING — set aging to {AGING_HIGH}s on {sw}")
    except Exception as e:
        print(f"  [ERROR] INCREASE_AGING failed: {e}")

def action_decrease_aging(sw):
    """Decrease MAC aging timer — entries expire faster, table stays fresher"""
    try:
        run_cmd(f"ovs-vsctl set Bridge {sw} other_config:mac-aging-time={AGING_LOW}")
        print(f"  [ACTION] DECREASE_AGING — set aging to {AGING_LOW}s on {sw}")
    except Exception as e:
        print(f"  [ERROR] DECREASE_AGING failed: {e}")

def execute_action(sw, action_idx, port=None):
    evicted_mac = None

    if action_idx == 0:
        action_learn_mac(sw)
    elif action_idx == 1:
        evicted_mac = action_evict_entry(sw)
    elif action_idx == 2:
        action_flood(sw)
    elif action_idx == 3:
        if port:
            action_block_port(sw, port)
        else:
            print(f"  [SKIP] BLOCK_PORT — no flooding port detected on {sw}")
    elif action_idx == 4:
        if port:
            action_unblock_port(sw, port)
        else:
            print(f"  [SKIP] UNBLOCK_PORT — no blocked port to release on {sw}")
    elif action_idx == 5:
        action_increase_aging(sw)
    elif action_idx == 6:
        action_decrease_aging(sw)

    return evicted_mac
