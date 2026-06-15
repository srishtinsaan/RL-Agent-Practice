def get_reward(
    action,
    old_fill,
    new_fill,
    old_flood,
    new_flood,
    old_age,
    new_age,
    all_ports_blocked=False
):

    mac_fill_improvement  = old_fill  - new_fill
    flood_gain = old_flood - new_flood
    age_gain   = old_age   - new_age

    reward = (
        0.8 * flood_gain +
        0.6 * mac_fill_improvement   +
        0.2 * age_gain
    )

    action_cost = {
        0: 0.01, #learn mac
        1: 0.05, #evict entry
        2: 0.15, #Flood
        3: 0.10, #block Port
        4: 0.05, #unblock port
        5: 0.05, #increase aging
        6: 0.05  #increase aging
    }

            # 0: 'LEARN_MAC',
            # 1: 'EVICT_ENTRY',
            # 2: 'FLOOD',
            # 3: 'BLOCK_PORT',
            # 4: 'UNBLOCK_PORT',
            # 5: 'INCREASE_AGING',
            # 6: 'DECREASE_AGING'

    reward -= action_cost[action]


# outcomes

    outcome = "neutral"

    if reward > 0.1:
        outcome = "improved"
    elif reward < -0.1:
        outcome = "degraded"

# situation

    situation = "NORMAL"

    # table overflow
    if new_fill >= 0.95:
        reward -= 0.7
        situation = "CRITICAL"

    # preventive entry removal before overflow
    elif new_fill >= 0.80:
        reward += 0.3
        situation = "PREVENTIVE"

    if all_ports_blocked:
        reward -= 1.0
        outcome = "isolation"

    reward = max(-1.0, min(1.0, reward))

    return reward, outcome, situation



























# def get_reward(
#     action,
#     old_fill,
#     new_fill,
#     old_flood,
#     new_flood,
#     old_age,
#     new_age,
#     all_ports_blocked=False
# ):

#     mac_gain = old_fill - new_fill
#     flood_gain = old_flood - new_flood
#     age_gain = old_age - new_age

#     reward = (
#         3.0 * flood_gain +
#         2.0 * mac_gain +
#         1.0 * age_gain
#     )

#     action_cost = {
#     0: 0.01,
#     1: 0.05,
#     2: 0.10,
#     3: 0.20,
#     4: 0.10,
#     5: 0.05,
#     6: 0.05
#     }

#     reward -= action_cost[action]

#     outcome = "neutral"

#     if reward > 0.2:
#         outcome = "improved"

#     elif reward < -0.2:
#         outcome = "degraded"

#     situation = "NORMAL"

#     if new_fill >= 0.95:
#         reward -= 5
#         situation = "CRITICAL"

#     elif new_fill >= 0.80:
#         situation = "PREVENTIVE"

#     if all_ports_blocked:
#         reward -= 10
#         outcome = "isolation"

#     return reward, outcome, situation