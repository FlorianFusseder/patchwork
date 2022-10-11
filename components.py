from typing import Type, Optional, Dict

import numpy as np

from pieces import p_arrays, b_array


def toASCII(shape):
    if shape.any():
        return str(shape).replace(' ', '').replace('[', '').replace(']', '').replace('0', ' ').replace('1', '█')


class Location:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class Piece:
    def __init__(self, id_, button_cost, time_cost, button_income, shape=None) -> None:
        self.id_ = id_
        self.button_cost = button_cost
        self.time_cost = time_cost
        self.button_income = button_income
        self.shape = np.array(shape)
        self.size = np.count_nonzero(self.shape)

    def __str__(self) -> str:
        return f"Id: {self.id_}, ButtonCost: {self.button_cost}, TimeCost: {self.time_cost}, " \
               f"Production: {self.button_income}, Size: {self.size}"

    def get_button_rate(self, remaining_income_phases) -> float:
        # Button-rate = [(size x 2) + (buttons x remaining income phases) - button cost] / time cost
        return ((self.size * 2) + (self.button_income * remaining_income_phases) - self.button_cost) / self.time_cost

    def show(self):
        copy = np.copy(self.shape)
        copy[copy == 1] = 255
        copy = np.array(copy, dtype=np.dtype('uint8'))
        from PIL import Image
        convert = Image.fromarray(copy, mode='L').convert('1')
        convert.resize(s * 40 for s in convert.size).show()


class Patches:

    def __init__(self, patches, token_position) -> None:
        self.collection = []
        self.token_position = token_position

        for id_, patch in patches.items():
            self.collection.append(Piece(id_, patch['button-cost'], patch['time-cost'], patch['income']))

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

    def __init__(self) -> None:
        self.track = []
        for i in range(53, -1, -1):
            self.track.append(TimeTrack.TimeTrackField(i))

    def get_remaining_income_phases(self, player) -> int:
        return player.time_count


class Player:
    class Board:

        def __init__(self) -> None:
            self.board = np.array(b_array)

        def __str__(self):
            return toASCII(self.board)

    def __init__(self, player_number: int, player_data: Dict):
        self.player_number = player_number
        self.player_name = player_data["name"]
        self.time_count = player_data["time_counter"]
        self.button_production = player_data["income_counter"]
        self.button_count = player_data["button_counter"]
        self.color_code = player_data["color_code"]
        self.player_turn = player_data["current_player"]
        self.player_track = TimeTrack()
        self.board = Player.Board()

    def __str__(self) -> str:
        return f"{self.player_name}"

    def status(self) -> str:
        return f"Player {self.player_number} {self.player_name}: Buttons: {self.button_count}, " \
               f"ButtonProduction: {self.button_production}, Time: {self.time_count}"

    def calculate_turn(self, patches: Patches) -> (Piece, Location):
        remaining_income_phases = self.player_track.get_remaining_income_phases(self)
        return patches[0], Location(0, 0)
