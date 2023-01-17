from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Dict, List, Set

import click
import numpy as np
from PIL import ImageColor


class Patch:

    def __init__(self, *args) -> None:
        if len(args) == 0:
            self.id_ = "special_patch"
            self.button_cost = 0
            self.time_cost = 0
            self.button_income = 0
            self.size = 1
        elif len(args) == 1:
            self.id_ = args[0]['key']
            self.button_cost = int(args[0]['cost'])
            self.time_cost = int(args[0]['time'])
            self.button_income = int(args[0]['income'])
            self.size = int(args[0]['spaces'])

    def __str__(self) -> str:
        return f"Id: {self.id_}, ButtonCost: {self.button_cost}, TimeCost: {self.time_cost}, " \
               f"Production: {self.button_income}, Size: {self.size}"

    def get_button_rate(self, remaining_income_phases, remaining_time, track) -> float:
        # Button-rate = [(size x 2) + (buttons x remaining income phases) - button cost] / time cost
        special_patch_factor = track.get_special_patch_factor(remaining_time, self.time_cost)
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
    special_patch = Patch()

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

    def take_patch(self, patch_to_take: TurnAction) -> Patch:
        taken_patch = self.collection.pop(int(patch_to_take + self.token_position))
        self.token_position += patch_to_take
        return taken_patch

    def __len__(self):
        return len(self.collection)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.collection[self.token_position + item]
        elif isinstance(item, slice):
            if len(self.collection) - self.token_position < item.stop - 1:
                raise IndexError
            return self.collection[item.start + self.token_position: item.stop + self.token_position: item.step]

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
        return sum(1 for location in self._income_locations if location > self.markers[player.player_id]['location'])

    def get_special_patch_factor(self, remaining_time, time_cost):
        start_time = self._goal_id - remaining_time
        next_time = start_time + time_cost
        for _special_spot_location in self._special_spot_locations:
            if start_time < _special_spot_location < next_time:
                return 2
        return 0

    def get_time(self, player):
        return self.markers[player.player_id]["location"]

    def get_remaining_time(self, player):
        return self._goal_id - self.get_time(player)

    def get_current_player_number(self):
        return min(self.markers.items(), key=lambda player: player[1]["location"] - player[1]["top"])[0]

    def get_sorted_player_order(self):
        return [player_tuple[0] for player_tuple in sorted(self.markers.items(), key=lambda player: player[1]["location"] - player[1]["top"])]

    def take_patch_action(self, patch: Patch) -> (bool, bool):
        """
        :return: (bool, bool)
        bool: Player gets income
        bool: Player receives a special 1x1 patch
        """
        player_order = self.get_sorted_player_order()
        trigger_income, trigger_special_patch = self.triggers_income_triggers_special_patch(self.markers[player_order[0]]["location"], patch.time_cost)
        self.markers[player_order[0]]["location"] += patch.time_cost
        if self.markers[player_order[0]]["location"] == self.markers[player_order[1]]["location"]:
            self.markers[player_order[0]]["top"] = 1
        else:
            self.markers[player_order[0]]["top"] = 0
        return trigger_income, trigger_special_patch

    def take_advance_action(self) -> (int, bool, bool):
        """
        :return: (int, bool)
        int: Button count which the player will receive through potentially triggered income phase
        bool: Player gets income
        bool: Player receives a special 1x1 patch
        """
        # todo check if the playerorder must be reversed
        player_order = self.get_sorted_player_order()
        buttons_to_receive: int = self.markers[player_order[1]]["location"] - self.markers[player_order[0]]["location"] + 1
        self.markers[player_order[0]]["location"] = self.markers[player_order[1]]["location"] + 1
        self.markers[player_order[0]]["top"] = 0
        trigger_income, trigger_special_patch = self.triggers_income_triggers_special_patch(self.markers[player_order[1]]["location"], buttons_to_receive)
        return buttons_to_receive, trigger_income, trigger_special_patch

    def triggers_income_triggers_special_patch(self, starting_position: int, steps_to_progress_on_track: int) -> (bool, bool):
        ending_position = starting_position + steps_to_progress_on_track

        def _triggers(l: [int]):
            for i in l:
                if i < starting_position:
                    continue
                elif i > ending_position:
                    return False
                else:
                    return True

        return _triggers(self._income_locations), _triggers(self._special_spot_locations)

    def game_end(self):
        return all((position >= self._goal_id for position in [player["location"] for player in self.markers.values()]))


class Player:

    def __init__(self, player_data: Dict):
        self.player_id = player_data["id"]
        self.player_number = int(player_data["no"])
        self.player_name = player_data["name"]
        self.button_production = int(player_data["income"])
        self.button_count = int(player_data["buttons"])
        self.color_code = player_data["color"]
        self.empty_spaces = int(player_data["empty_spaces"])
        self.owns_special7x7 = player_data["tile_special7x7"]

        self.owned_patches: Set[Patch] = player_data["owned_patches"]

    def __str__(self) -> str:
        return f"{self.player_name}"

    def status(self, track: TimeTrack) -> str:
        return f"Player {self.player_id} {self.player_name}: Buttons: {self.button_count}, " \
               f"ButtonProduction: {self.button_production}, Time: {track.get_time(self)}, EmptySpaces: {self.empty_spaces}"

    def get_current_score(self, track):
        return -(self.empty_spaces * 2) \
               + self.button_count \
               + self.button_production * track.get_remaining_income_phases(self) \
               + 0 if not self.owns_special7x7 else 7

    def my_turn(self, track: TimeTrack) -> bool:
        return self.player_id == track.get_current_player_number()

    def get_player_color(self):
        return ImageColor.getcolor(f"#{self.color_code}", "RGB")

    def __handle_triggers(self, triggers_income: bool, triggers_special_patch: bool):
        if triggers_income:
            self.button_count += self.button_production
        if triggers_special_patch:
            self.owned_patches.add(Market.special_patch)

    def __recalculate_empty_spaces(self):
        self.empty_spaces = 81 - sum([patch.size for patch in self.owned_patches])

    def take_patch_action(self, patch: Patch, triggers_income: bool, triggers_special_patch: bool):
        self.button_count -= patch.button_cost
        self.button_production += patch.button_income
        self.owned_patches.add(patch)
        self.__handle_triggers(triggers_income, triggers_special_patch)
        self.__recalculate_empty_spaces()

    def receive_buttons(self, button_to_receive, triggers_income: bool, triggers_special_patch: bool):
        self.button_count += button_to_receive
        self.__handle_triggers(triggers_income, triggers_special_patch)
        if triggers_special_patch:
            self.__recalculate_empty_spaces()

    def can_afford_patch(self, patch: Patch):
        return self.button_count >= patch.button_cost


class TurnAction(IntEnum):
    PATCH_1 = 0,
    PATCH_2 = 1,
    PATCH_3 = 2,
    ADVANCE = 3,


class AbstractGameState(ABC):

    @property
    @abstractmethod
    def p1(self) -> Player:
        pass

    @property
    @abstractmethod
    def p2(self) -> Player:
        pass

    @property
    @abstractmethod
    def market(self) -> Market:
        pass

    @property
    @abstractmethod
    def time_track(self) -> TimeTrack:
        pass

    @property
    @abstractmethod
    def history(self) -> [(Player, TurnAction, int, int)]:
        pass

    @abstractmethod
    def execute_turn(self, turn_action: TurnAction):
        pass

    @abstractmethod
    def get_final_score(self) -> (int, int):
        pass

    @abstractmethod
    def get_active_player(self) -> Player:
        pass

    @abstractmethod
    def turn_action_possible(self, turn_action) -> bool:
        pass

    @abstractmethod
    def player1s_turn(self) -> bool:
        pass

    @abstractmethod
    def print_outcome(self):
        pass


class GameState(AbstractGameState):

    @property
    def p1(self) -> Player:
        return self._p1

    @property
    def p2(self) -> Player:
        return self._p2

    @property
    def market(self) -> Market:
        return self._market

    @property
    def time_track(self) -> TimeTrack:
        return self._track

    @property
    def history(self) -> [(Player, TurnAction, int, int)]:
        return self._history

    def __init__(self, p1: Player, p2: Player, market: Market, track: TimeTrack):
        self._p1 = p1
        self._p2 = p2
        self._market = market
        self._track = track
        self._history: [TurnAction] = []

    def __take_patch(self, player: Player, action: TurnAction):
        patch = self._market.take_patch(action)
        trigger_income, trigger_special_patch = self._track.take_patch_action(patch)
        player.take_patch_action(patch, trigger_income, trigger_special_patch)

    def __advance(self, player: Player):
        received_button_count, trigger_income, trigger_special_patch = self._track.take_advance_action()
        player.receive_buttons(received_button_count, trigger_income, trigger_special_patch)

    def execute_turn(self, turn_action: TurnAction):
        player: Player = self.get_active_player()
        if turn_action == TurnAction.ADVANCE:
            self.__advance(player)
        else:
            self.__take_patch(player, turn_action)
        self._history.append((player, turn_action, self._p1.get_current_score(self._track), self.p2.get_current_score(self._track)))

    def get_final_score(self) -> (int, int):
        return self.history[-1][2], self.history[-1][3]

    def get_active_player(self) -> Player:
        player_number = self._track.get_current_player_number()
        return self._p1 if self._p1.player_id == player_number else self._p2

    def turn_action_possible(self, turn_action):
        match turn_action:
            case TurnAction.ADVANCE:
                return True
            case TurnAction.PATCH_1 | TurnAction.PATCH_2 | TurnAction.PATCH_3:
                patch_index = int(turn_action)
                if not len(self._market) >= patch_index + 1:
                    return False
                patch: Patch = self._market[patch_index]
                player: Player = self.get_active_player()
                return player.can_afford_patch(patch)
            case _:
                raise NotImplementedError(f"{turn_action} not yet implemented")

    def player1s_turn(self) -> bool:
        return self._track.get_current_player_number() == self._p1.player_id

    def print_outcome(self):
        click.echo(f"Best Turn choice: {self.history[0][1].name}")

        def get_color(p1_, p2_):
            if p1_ > p2_:
                return 'green'
            elif p1_ < p2_:
                return 'red'
            else:
                return 'yellow'

        def print_(p1_, p1_score, p2_score):
            click.secho(f"{p1_.player_name}", fg=p1_.get_player_color(), nl=False)
            click.echo("'s score: ", nl=False)
            click.secho(p1_score, bg=(get_color(p1_score, p2_score)), fg='black')

        p1_score = self._p1.get_current_score(self._track)
        p2_score = self._p2.get_current_score(self._track)

        print_(self._p1, p1_score, p2_score)
        print_(self._p2, p2_score, p1_score)

        click.echo()
        click.echo("Calculated Path:")
        for player, turn_action, p1_score, p2_score in self.history:
            click.echo(f"{player.player_name}'s turn: {turn_action.name} ({self._p1.player_name}: {p1_score}, {self._p2.player_name}: {p2_score})")

        click.echo()


class NoopGameState(AbstractGameState):

    @property
    def market(self) -> Market:
        pass

    @property
    def time_track(self) -> TimeTrack:
        pass

    @property
    def history(self) -> [(Player, TurnAction, int, int)]:
        pass

    @property
    def p1(self) -> Player:
        pass

    @property
    def p2(self) -> Player:
        pass

    def __int__(self):
        pass

    def turn_action_possible(self, turn_action) -> bool:
        pass

    def get_active_player(self) -> Player:
        pass

    def execute_turn(self, turn_action: TurnAction):
        pass

    def get_final_score(self) -> (int, int):
        return -158, -158

    def player1s_turn(self) -> bool:
        return True

    def print_outcome(self):
        pass
