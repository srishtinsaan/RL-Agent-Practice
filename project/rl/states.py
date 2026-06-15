class LiveStateEncoder:
    def __init__(self, bins=8):
        self.bins = bins
        self.interval = 1.0 / self.bins # 0.125

    def binning(self, value): 
        bin_index = int(value / self.interval) # 0.625/0.125 = 5.04 => 5
        # it truncates so bin 0 range [0.000 - 0.125) like this others

# ####################



        # Handle value = 1.0 case 
        # if value = 1 then bin_index = 8 but our bins are from 0 to 7 so keep it in bin 7
        bin_value = min(bin_index, self.bins - 1)
        return bin_value

    def get_state_index(self, state_info):
        mac_bin = self.binning(state_info["mac_fill"])
        flood_bin = self.binning(state_info["flood_pressure"])
        age_bin = self.binning(state_info["avg_age"])

        state_index = (
            mac_bin * self.bins * self.bins
            + flood_bin * self.bins
            + age_bin
        )

        return state_index

    def get_bin_name(self, bin_number):
        interval = 1.0 / self.bins
        start = bin_number * interval
        end = start + interval
        if bin_number == self.bins - 1:
            end = 1.
        return f"Bin {bin_number}: [{start:.3f}, {end:.3f}]"

    def display_bins_with_intervals(self):
        interval = 1.0 / self.bins
        for i in range(self.bins):
            start = i * interval
            if i == self.bins - 1:
                end = 1.0
            else:
                end = (i + 1) * interval
            print(f"Bin {i}: {start:.3f} - {end:.3f}")

    def total_states(self):
        return self.bins ** 3
    
    def decode_state_index(self, state_idx):
        return self.state_space[state_idx]