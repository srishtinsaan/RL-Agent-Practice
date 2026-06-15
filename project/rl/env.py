import subprocess
import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project.get_data import (
    get_normalized_state
)

from project.rl.action_definition import execute_action
from project.rl.reward import get_reward
from project.rl.actions import ActionSpace

"""
    Reads live network state
    Applies RL actions safely (with guards)
    omputes reward + next state transition
"""

class LiveEnv:
    def __init__(self, switch=None):
        self.switch = switch or "g0_s1"
        self.prev_mac_entries = {}
        print(f"[OK] env.py :: Connected to switch: {self.switch}")

        try:
            bridges = subprocess.check_output(
                ["ovs-vsctl", "list-br"], text=True
            ).split()
            if not bridges:
                raise RuntimeError(
                    "No OVS switches found. Start Mininet first."
                )
            

        except FileNotFoundError:
            raise RuntimeError(
                "\n[ERROR] ovs-vsctl not found.\n"
            )
           
        
    def get_live_state(self):

        mac_fill_val, flood_val, age_val, mac_entries = get_normalized_state(
            self.switch,
            self.prev_mac_entries    # ← pass previous snapshot
        )

        self.prev_mac_entries = mac_entries   

        return {
            "mac_fill":       mac_fill_val,
            "flood_pressure": flood_val,
            "avg_age":        age_val,
            "mac_entries":    mac_entries
        }
    
    def step(self, action):

        state_info = self.get_live_state()
        original_action = action

    #
    # Guard:
    #   

        # Don't evict when table is nearly empty
        if action == 0 and state_info["mac_fill"] < 0.20:
            action = 2  # switch to increase aging

        if action == 1 and state_info["flood_pressure"] > 0.6:
            action = 0  # evict instead

        if action == 2 and state_info["mac_fill"] >= 0.95:
            action = 0  # evict instead

        # Don't rebalance when table is nearly empty
        if action == 3 and state_info["mac_fill"] < 0.20:
            action = 1  # increase aging instead

        executed_action = action

        result = execute_action(self.switch, executed_action, state_info["flood_pressure"])

        # if executed_action in [0, 1]:
        #     time.sleep(3)
        # else:
        time.sleep(1)
        next_state_info = self.get_live_state()

        fill_change  = round(next_state_info["mac_fill"]       - state_info["mac_fill"],       4)
        flood_change = round(next_state_info["flood_pressure"] - state_info["flood_pressure"], 4)

        print(
        f"[STATE] "
        f"Fill {state_info['mac_fill']:.3f}"
        f"->{next_state_info['mac_fill']:.3f} | "
        f"Flood {state_info['flood_pressure']:.3f}"
        f"->{next_state_info['flood_pressure']:.3f} | "
        f"Age {state_info['avg_age']:.3f}"
        f"->{next_state_info['avg_age']:.3f}"
        )

        reward, outcome, situation = get_reward(
            action=executed_action,

            old_fill=state_info["mac_fill"],
            new_fill=next_state_info["mac_fill"],

            old_flood=state_info["flood_pressure"],
            new_flood=next_state_info["flood_pressure"],

            old_age=state_info["avg_age"],
            new_age=next_state_info["avg_age"],

        )


        info = {
            "action_name":     ActionSpace.get_action_name(executed_action),
            "original_action": original_action,
            "executed_action": executed_action,
            "mac_count":       len(next_state_info["mac_entries"]),
            "mac_fill":        next_state_info["mac_fill"],
            "fill_change":     fill_change,
            "flood_pressure":  next_state_info["flood_pressure"],
            "flood_change":    flood_change,
            "avg_age":         next_state_info["avg_age"],
            "outcome":         outcome,
            "situation":       situation,
            "action_result":   result if result else "N/A"
        }
        
        return next_state_info, reward, info