import sys, os
import csv
sys.path.append(os.path.dirname(__file__))
from project.rl.env import LiveEnv
from project.rl.states import LiveStateEncoder
from project.rl.agent import QAgent

def run_live_training(switch='g0_s0', episodes=200, steps_per_ep=30):
    # ep = 200
    # steps = 30
    
    env     = LiveEnv(switch=switch)
    encoder = LiveStateEncoder(bins=8)
    agent   = QAgent(states=encoder.total_states(), actions=7)

    log_path = 'project/results/logs/live_step_log.csv'
    os.makedirs('project/results/logs', exist_ok=True)


    # per step q table
    qtable_path = 'project/results/qtable/q_table.csv'
    os.makedirs('project/results/qtable', exist_ok=True)

    episode_log_path = 'project/results/logs/episode_log.csv'

    with open(log_path, 'w', newline='') as f:
        writer = csv.writer(f)      
        writer.writerow([
            'Episode',
            'Step',

            'mac_fill',
            'MAC_Count',
            'flood_pressure',
            'age_score',

            'Situation',
            'State_Index',

            'Original_Action',
            'Executed_Action',
            'Action_Name',

            'Q_LEARN',
            'Q_EVICT',
            'Q_FLOOD',
            'Q_BLOCK',
            'Q_UNBLOCK',
            'Q_INC_AGE',
            'Q_DEC_AGE',

            'Chosen_By',
            'Outcome',
            'Reward',

            'Total_Ep_Reward',
            'Epsilon',

            'Port_Acted',
            'Currently_Blocked',
            'Evicted_MAC',

            'Old_MAC_Fill',
            'New_MAC_Fill',

            'Old_Flood',
            'New_Flood',

            'Old_Age',
            'New_Age'
            ])
    
    with open(qtable_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Q_LEARN',
            'Q_EVICT',
            'Q_FLOOD',
            'Q_BLOCK',
            'Q_UNBLOCK',
            'Q_INC_AGE',
            'Q_DEC_AGE'])

    rewards_history = []

    
    
    # G
    with open(episode_log_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Episode', 'Discounted_G', 'Total_Reward', 'Epsilon'])

    for ep in range(episodes):
        state_info   = env.get_live_state()
        state_idx    = encoder.get_state_index(state_info)
        total_reward = 0
        episode_rewards = []

        for step in range(steps_per_ep):
            is_random, action             = agent.choose_action_with_flag(state_idx)
            
            old_state_info = state_info.copy()
            next_state_info, reward, info = env.step(action)
            next_state_idx                = encoder.get_state_index(next_state_info)
            executed_action               = info["executed_action"]

            # FIX: update on executed_action, not original action
            agent.update(state_idx, executed_action, reward, next_state_idx)

            q_values     = agent.get_q_values(state_idx)
            state_idx    = next_state_idx
            state_info   = next_state_info
            total_reward += reward
            episode_rewards.append(reward) #for discounted reward

            # LOG every step
            with open(log_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    ep + 1,
                    step + 1,

                    info['mac_fill'],
                    info['mac_count'],
                    info['flood_pressure'],
                    info['age_score'],

                    info['situation'],
                    state_idx,

                    info['original_action'],
                    info['executed_action'],
                    info['action_name'],

                    round(q_values[0], 4),
                    round(q_values[1], 4),
                    round(q_values[2], 4),
                    round(q_values[3], 4),
                    round(q_values[4], 4),
                    round(q_values[5], 4),
                    round(q_values[6], 4),

                    'RANDOM' if is_random else 'GREEDY',

                    info['outcome'],
                    round(reward, 4),

                    round(total_reward, 4),
                    round(agent.epsilon, 4),

                    info.get('port_acted', 'N/A'),
                    info.get('currently_blocked', '[]'),
                    info.get('evicted_mac', 'N/A'),

                    old_state_info["mac_fill"],
                    next_state_info["mac_fill"],

                    old_state_info["flood_pressure"],
                    next_state_info["flood_pressure"],

                    old_state_info["age_score"],
                    next_state_info["age_score"]
                ])

                state_info = next_state_info

            with open(qtable_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    round(q_values[0], 4),
                    round(q_values[1], 4),
                    round(q_values[2], 4),
                    round(q_values[3], 4),
                    round(q_values[4], 4),
                    round(q_values[5], 4),
                    round(q_values[6], 4)
                ])

            print(
                f"  Ep {ep+1} | Step {step+1} | "
                f"{info['action_name']:15s} | "
                f"{info['outcome']:20s} | "
                f"Reward: {reward:+.2f} | "
                f"ε: {agent.epsilon:.3f}"
            )
        
        # discounted return
        G = 0
        for r in reversed(episode_rewards):
            G = r + agent.gamma * G
            
        print(f"Ep {ep+1} | Discounted Return G: {G:.4f}")

        with open(episode_log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([ep + 1, round(G, 4), round(total_reward, 4), round(agent.epsilon, 4)])

        agent.decay_epsilon()
        rewards_history.append(total_reward)

        # Final q table generated after training
        print(f"\nEp {ep+1}/{episodes} | Total Reward: {total_reward:+.2f}\n")

        with open(qtable_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['State_Index', 'mac_bin', 'flood_bin', 'age_bin',
                             'Q_LEARN', 'Q_EVICT', 'Q_FLOOD', 'Q_BLOCK',
                             'Q_UNBLOCK', 'Q_INC_AGE', 'Q_DEC_AGE'])
            for state_idx in range(encoder.total_states()):
                m, fl, a = encoder.decode_state_index(state_idx)
                q = agent.get_q_values(state_idx)
                writer.writerow([
                    state_idx, m, fl, a,
                    round(q[0],4), round(q[1],4), round(q[2],4),
                    round(q[3],4), round(q[4],4), round(q[5],4), round(q[6],4)
                ])


    return agent, encoder, rewards_history