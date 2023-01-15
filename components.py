from typing import Dict, List

import numpy as np
from PIL import ImageColor


class Patch:
    def __init__(self, patch_data) -> None:
        self.id_ = patch_data['key']
        self.button_cost = int(patch_data['cost'])
        self.time_cost = int(patch_data['time'])
        self.button_income = int(patch_data['income'])
        self.size = int(patch_data['spaces'])

    def __str__(self) -> str:
        return f"Id: {self.id_}, ButtonCost: {self.button_cost}, TimeCost: {self.time_cost}, " \
               f"Production: {self.button_income}, Size: {self.size}"

    def get_button_rate(self, remaining_income_phases, remaining_time, track) -> float:
        # Button-rate = [(size x 2) + (buttons x remaining income phases) - button cost] / time cost
        special_patch_factor = track.triggers_special_patch(remaining_time, self.time_cost)
        time_cost = remaining_time if self.time_cost > remaining_time else self.time_cost
        return (self.size * 2 + (
                self.button_income * remaining_income_phases) - self.button_cost + special_patch_factor) / time_cost

    def show(self):
        copy = np.copy(self.shape)
        copy[copy == 1] = 255
        copy = np.array(copy, dtype=np.dtype('uint8'))
        from PIL import Image
        convert = Image.fromarray(copy, mode='L').convert('1')
        convert.resize(s * 40 for s in convert.size).show()


class Market:
    patch_keys = {
        "patch_1", "patch_2", "patch_3", "patch_4", "patch_5", "patch_6", "patch_7", "patch_8", "patch_9",
        "patch_10", "patch_11", "patch_12", "patch_13", "patch_14", "patch_15", "patch_16", "patch_17",
        "patch_18", "patch_19", "patch_20", "patch_21", "patch_22", "patch_23", "patch_24", "patch_25",
        "patch_26", "patch_27", "patch_28", "patch_29", "patch_30", "patch_31", "patch_32", "patch_33"
    }

    special_patch_keys = {"patch_0_0", "patch_0_1", "patch_0_2", "patch_0_3", "patch_0_4"}

    def __init__(self, patches, token_position) -> None:
        self.collection = []
        self.token_position = int(token_position)

        for patch in [patch for patch in sorted(patches.values(), key=lambda item: int(item['state'])) if
                      patch['location'] == 'market']:
            self.collection.append(Patch(patch))

    def get_next_three(self) -> List[Patch]:
        return self.collection[self.token_position:self.token_position + 3]

    def __len__(self):
        return len(self.collection)

    def __getitem__(self, item):
        return self.collection[item]

    def __str__(self) -> str:
        return "\n".join([str(p) for p in self.collection])


class TimeTrack:
    _goal_id = 53
    _income_locations = [5, 11, 17, 23, 29, 35, 41, 47, _goal_id]
    _special_spot_locations = [26, 32, 38, 44, 50]

    class TimeTrackField:
        def __init__(self, id_: int) -> None:
            self.is_goal = id_ == TimeTrack._goal_id
            self.trigger_income = id_ in TimeTrack._income_locations
            self.trigger_special_spot_income = id_ in TimeTrack._special_spot_locations
            self.id_ = id_

    def __init__(self, player_list) -> None:
        self.track = []
        for i in range(53, -1, -1):
            self.track.append(TimeTrack.TimeTrackField(i))

        self.markers = {}
        for player in player_list:
            self.markers[player["id"]] = {
                "location": int(player["time_marker"]["location"]),
                "top": int(player["time_marker"]["top"])
            }

    def get_remaining_income_phases(self, player) -> float:
        return sum(
            1 for location in self._income_locations if location > self.markers[player.player_number]['location'])

    def triggers_special_patch(self, remaining_time, time_cost):
        start_time = self._goal_id - remaining_time
        next_time = start_time + time_cost
        for _special_spot_location in self._special_spot_locations:
            if start_time < _special_spot_location < next_time:
                return 2
        return 0

    def get_time(self, player):
        return self.markers[player.player_number]["location"]

    def get_remaining_time(self, player):
        return self._goal_id - self.get_time(player)

    def get_current_player_number(self):
        return min(self.markers.items(), key=lambda player: player[1]["location"] - player[1]["top"])[0]


class Player:
    def __init__(self, player_data: Dict, track: TimeTrack):
        self.player_number = player_data["id"]
        self.player_name = player_data["name"]
        self.button_production = int(player_data["income"])
        self.button_count = int(player_data["buttons"])
        self.color_code = player_data["color"]
        self.empty_spaces = int(player_data["empty_spaces"])
        self.owns_special7x7 = player_data["tile_special7x7"]

        self.owned_patches = player_data["owned_patches"]
        self.track = track

        self.score = self.calculate_current_score()

    def __str__(self) -> str:
        return f"{self.player_name}"

    def status(self) -> str:
        return f"Player {self.player_number} {self.player_name}: Buttons: {self.button_count}, " \
               f"ButtonProduction: {self.button_production}, Time: {self.track.get_time(self)}, EmptySpaces: {self.empty_spaces}"

    def calculate_turn(self, patches: Market) -> Dict:
        results = {
            'winner-index': None,
            0: {},
            1: {},
            2: {},
        }
        three_patches = patches.get_next_three()
        winner_rate = None

        for i, patch in enumerate(three_patches):
            rate = patch.get_button_rate(self.track.get_remaining_income_phases(self),
                                         self.track.get_remaining_time(self),
                                         self.track)
            affordable = patch.button_cost <= self.button_count
            results[i]['button-rate'] = rate
            results[i]['affordable'] = affordable
            results[i]['patch'] = patch
            if affordable and (not winner_rate or rate > winner_rate) and rate > 1:
                winner_rate = rate
                results['winner-index'] = i
        return results

    def calculate_current_score(self):
        return -(self.empty_spaces * 2) \
               + self.button_count \
               + self.button_production * self.track.get_remaining_income_phases(self) \
               + 0 if not self.owns_special7x7 else 7

    def my_turn(self):
        return self.player_number == self.track.get_current_player_number()

    def get_player_color(player):
        return ImageColor.getcolor(f"#{player.color_code}", "RGB")
