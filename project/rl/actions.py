class ActionSpace:

    ACTIONS = {
        0: "EVICT",
        1: "INCREASE_AGING",
        2: "DECREASE_AGING",
        3: "REBALANCE"
    }

    @staticmethod
    def get_all_actions():
        return list(ActionSpace.ACTIONS.keys())

    @staticmethod
    def get_action_name(action_idx):
        return ActionSpace.ACTIONS.get(
            action_idx,
            "UNKNOWN"
        )

    @staticmethod
    def get_action_count():
        return len(ActionSpace.ACTIONS)

    @staticmethod
    def is_valid_action(action_idx):
        return action_idx in ActionSpace.ACTIONS