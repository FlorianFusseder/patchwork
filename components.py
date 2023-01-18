from __future__ import annotations

from enum import IntEnum
from typing import Dict, Set, Optional

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

    class LinkedPatchList:

        def __init__(self):
            self.__head: Market.LinkedPatchList.Node = None
            self.__tail: Market.LinkedPatchList.Node = None
            self.__length = 0

        class Node:
            def __init__(self, patch: Patch):
                self.patch: Patch = patch
                self.next: Optional[Market.LinkedPatchList.Node] = None

        def append(self, patch: Patch):
            self.__length += 1
            new_patch_node = Market.LinkedPatchList.Node(patch)
            if not self.__head:
                self.__head = new_patch_node
                self.__tail = new_patch_node
            else:
                self.__tail.next = new_patch_node
                self.__tail = new_patch_node

        def pop(self, index: int):
            if index > self.__length:
                raise IndexError("Not enough elements left in LinkedList")
            self.__length -= 1

            for i in range(index, 0, -1):
                new_head = self.__head.next
                to_tail = self.__head
                self.__head = new_head

                to_tail.next = None
                self.__tail.next = to_tail
                self.__tail = to_tail

            new_head = self.__head.next
            patch = self.__head.patch
            self.__head = new_head
            return patch

        def __len__(self):
            return self.__length

        def __getitem__(self, item):
            if isinstance(item, int):
                node = self.__head
                for i in range(0, item):
                    node = node.next
                return node.patch
            elif isinstance(item, slice):
                patch_list = []
                temp_head = self.__head
                for i in range(slice.start):
                    if temp_head.next:
                        temp_head = temp_head.next
                    else:
                        raise IndexError()

                for i in range(slice.start, slice.stop):
                    if slice.step and i % slice.step != 0:
                        continue

                    patch_list.append(temp_head.patch)
                    if temp_head.next:
                        temp_head = temp_head.next
                    else:
                        raise IndexError

                return patch_list

        def __repr__(self):
            st_repr = ""
            next_ = self.__head
            while next_.next:
                st_repr += str(next_.patch) + "\n"
                next_ = next_.next

            st_repr += str(next_.patch) + "\n"

            return st_repr

    def __init__(self, patches, token_position) -> None:
        self.__linked_patch_list = Market.LinkedPatchList()
        token_position = int(token_position)
        market_list = [patch for patch in sorted(patches.values(), key=lambda item: int(item['state'])) if patch['location'] == 'market']

        for patch in market_list[token_position:] + market_list[0:token_position]:
            self.__linked_patch_list.append(Patch(patch))

    def take_patch(self, patch_to_take: TurnAction) -> Patch:
        return self.__linked_patch_list.pop(patch_to_take)

    def __getitem__(self, item):
        return self.__linked_patch_list[item]

    def __str__(self) -> str:
        return "\n".join([str(p) for p in self.__linked_patch_list])

    def __len__(self):
        return len(self.__linked_patch_list)


class TimeTrack:
    _goal_id = 53
    _income_locations = [5, 11, 17, 23, 29, 35, 41, 47, _goal_id]
    _special_spot_locations = [26, 32, 38, 44, 50]

    def get_remaining_income_phases(self, player) -> float:
        return sum(1 for location in self._income_locations if location > player.location)

    def take_patch_action(self, active_player: Player, passive_player: Player, patch: Patch) -> (bool, bool):
        """
        :return: (bool, bool)
        bool: Player gets income
        bool: Player receives a special 1x1 patch
        """
        trigger_income, trigger_special_patch = self.triggers_income_triggers_special_patch(active_player.location, patch.time_cost)
        active_player.location += patch.time_cost
        active_player.location_top = 1 if active_player.location == passive_player.location else 0
        return trigger_income, trigger_special_patch

    def take_advance_action(self, active_player: Player, passive_player: Player) -> (int, bool, bool):
        """
        :return: (int, bool)
        int: Button count which the player will receive through potentially triggered income phase
        bool: Player gets income
        bool: Player receives a special 1x1 patch
        """
        buttons_to_receive: int = passive_player.location - active_player.location + 1
        trigger_income, trigger_special_patch = self.triggers_income_triggers_special_patch(active_player.location, buttons_to_receive)
        active_player.location = passive_player.location + 1
        active_player.location_top = 0
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

    def game_end(self, p1: Player, p2: Player):
        return p1.location >= self._goal_id and p2.location >= self._goal_id


class Player:

    @property
    def player_turn(self):
        # Initial Player turn - do not change
        return self.__player_turn

    def __init__(self, player_data: Dict, patch_data: Dict):
        self.player_id = player_data["id"]
        self.player_number = int(player_data["no"])
        self.__player_turn = player_data["players_turn"]
        self.player_name = player_data["name"]
        self.button_production = int(player_data["income"])
        self.button_count = int(player_data["buttons"])
        self.color_code = player_data["color"]
        self.empty_spaces = int(player_data["empty_spaces"])
        self.owns_special7x7 = player_data["tile_special7x7"]

        self.owned_patches: Set[Patch] = {Patch(patch_data[patch_name]) for patch_name in player_data["owned_patches"]}

        self.location = int(player_data["time_marker"]["location"])
        self.location_top = int(player_data["time_marker"]["top"])

    def __str__(self) -> str:
        return f"{self.player_name}"

    def status(self, track: TimeTrack) -> str:
        return f"Player {self.player_id} {self.player_name}: Buttons: {self.button_count}, " \
               f"ButtonProduction: {self.button_production}, Time: {self.location}, EmptySpaces: {self.empty_spaces}"

    def get_current_score(self, track):
        return -(self.empty_spaces * 2) \
               + self.button_count \
               + self.button_production * track.get_remaining_income_phases(self) \
               + 0 if not self.owns_special7x7 else 7

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


class GameState:

    @property
    def player(self) -> Player:
        return self.active_player if self.active_player.player_turn else self.passive_player

    @property
    def opponent(self) -> Player:
        return self.active_player if not self.active_player.player_turn else self.passive_player

    @property
    def active_player(self) -> Player:
        return self._active_player

    @property
    def passive_player(self) -> Player:
        return self._passive_player

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
        self._active_player: Player
        self._passive_player: Player

        if p1.player_turn:
            self._active_player = p1
            self._passive_player = p2
        else:
            self._active_player = p2
            self._passive_player = p1

        self._market: Market = market
        self._track: TimeTrack = track
        self._history: [(Player, TurnAction, int, int)] = []

    def __take_patch(self, player: Player, action: TurnAction):
        patch = self._market.take_patch(action)
        trigger_income, trigger_special_patch = self._track.take_patch_action(self.active_player, self.passive_player, patch)
        player.take_patch_action(patch, trigger_income, trigger_special_patch)

    def __advance(self, player: Player):
        received_button_count, trigger_income, trigger_special_patch = self._track.take_advance_action(self.active_player, self.passive_player)
        player.receive_buttons(received_button_count, trigger_income, trigger_special_patch)

    def execute_turn(self, turn_action: TurnAction):
        if turn_action == TurnAction.ADVANCE:
            self.__advance(self.active_player)
        else:
            self.__take_patch(self.active_player, turn_action)
        self._history.append({
            self.active_player.player_number: self.active_player.get_current_score(self._track),
            self.passive_player.player_number: self.passive_player.get_current_score(self._track),
            "player_turn": self.active_player.player_number,
            "turn_action": turn_action
        })

    def determine_active_player(self):
        if self.active_player.location - self.active_player.location_top > self.passive_player.location - self.passive_player.location_top:
            temp = self._active_player
            self._active_player = self.passive_player
            self._passive_player = temp

    def turn_action_possible(self, turn_action):
        match turn_action:
            case TurnAction.ADVANCE:
                return True
            case TurnAction.PATCH_1 | TurnAction.PATCH_2 | TurnAction.PATCH_3:
                patch_index = int(turn_action)
                if not len(self._market) >= patch_index + 1:
                    return False
                patch: Patch = self._market[patch_index]
                return self.active_player.can_afford_patch(patch)
            case _:
                raise NotImplementedError(f"{turn_action} not yet implemented")

    def print_outcome(self):
        click.secho(f"Best Turn choice: ", nl=False)
        click.secho(f"{self.history[0]['turn_action'].name}", blink=True)

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
            click.secho(p1_score, bg=(get_color(p1_score, p2_score)), fg='black', underline=True)

        p1_score = self.active_player.get_current_score(self._track)
        p2_score = self.passive_player.get_current_score(self._track)

        print_(self.active_player, p1_score, p2_score)
        print_(self.passive_player, p2_score, p1_score)

        click.echo()
        click.echo("Calculated Path:")
        for item in self.history:
            player_name = self.active_player.player_name if self.active_player.player_number == item["player_turn"] else self.passive_player.player_name
            click.echo(f"{player_name}'s turn: {item['turn_action'].name} ({self.player.player_name}: "
                       f"{item[self.player.player_number]}, {self.opponent.player_name}: {item[self.opponent.player_number]})")

        click.echo()

    def game_end(self):
        return self._track.game_end(self.active_player, self.passive_player)
