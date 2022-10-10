import numpy as np

from pieces import p_arrays, b_array


class Location:

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class Piece:
    def __init__(self, id_, button_cost, time_cost, production, shape) -> None:
        self.id_ = id_
        self.button_cost = button_cost
        self.time_cost = time_cost
        self.production = production
        self.shape = np.array(shape)
        self.size = np.count_nonzero(self.shape)

    def __str__(self) -> str:
        return f"Id: {self.id_}, ButtonCost: {self.button_cost}, TimeCost: {self.time_cost}, " \
               f"Production: {self.production}, Size: {self.size}" \
               f"\n {str(self.shape).replace('[', '').replace(']', '')}"

    def show(self):
        copy = np.copy(self.shape)
        copy[copy == 1] = 255
        copy = np.array(copy, dtype=np.dtype('uint8'))
        from PIL import Image
        convert = Image.fromarray(copy, mode='L').convert('1')
        convert.resize(s * 40 for s in convert.size).show()


class Pieces:

    def __init__(self) -> None:
        self.collection = []

        for i, p in p_arrays.items():
            self.collection.append(Piece(i, p[0], p[1], p[2], p[3]))

    def remove_piece(self, piece):
        pass

    def __len__(self):
        return len(self.collection)

    def __getitem__(self, item):
        return self.collection[item]

    def __str__(self) -> str:
        return "\n".join([str(p) for p in self.collection])


class Player:
    class Board:

        def __init__(self) -> None:
            self.board = np.array(b_array)

    def __init__(self, player_number: int, player_name: str):
        self.player_name = player_name
        self.player_number = player_number
        self.player_token = TimeTrack.TimeTrackToken(player_number)
        self.button_production = 0
        self.button_count = 5

    def __str__(self) -> str:
        return f"{self.player_number}"

    def status(self) -> str:
        return f"Player {self.player_number} ({self.player_name}): Buttons: {self.button_count}, Token: ({self.player_token})"

    def calculate_turn(self, pieces: Pieces) -> (Piece, Location):
        pass

    def calculate_bonus_turn(self):
        pass

    def put_piece(self, piece, location):
        pass


class TimeTrack:
    _goal_id = 53
    _income_locations = [5, 11, 17, 23, 29, 35, 41, 47, _goal_id]
    _special_spot_locations = [26, 32, 38, 44, 50]

    class TimeTrackToken:

        def __init__(self, player_number: int) -> None:
            self.distance = 0
            self.on_top = player_number == 1

        def __gt__(self, other):
            return self.distance > other.distance or self.distance == other.distance and self.on_top

        def __lt__(self, other):
            return self.distance < other.distance or self.distance == other.distance and not self.on_top

        def __str__(self) -> str:
            return f"Distance: {self.distance} Top: {self.on_top}"

    class TimeTrackField:
        def __init__(self, id_: int) -> None:
            self.is_goal = id_ == TimeTrack._goal_id
            self.trigger_income = id_ in TimeTrack._income_locations
            self.trigger_special_spot_income = id_ in TimeTrack._special_spot_locations
            self.id_ = id_

        def visit(self, player: Player):
            pass

    def __init__(self, p1: Player, p2: Player) -> None:
        self.track = []
        for i in range(54):
            self.track.append(TimeTrack.TimeTrackField(i))
        self.p1_token = p1.player_token
        self.p2_token = p2.player_token

    def done(self) -> bool:
        return self.p1_token.distance == self._goal_id and self.p2_token == self._goal_id

    def advance_player(self, active_player: Player, piece: Piece) -> Piece:
        return Piece()
