import copy
from abc import ABC, abstractmethod
from multiprocessing import Pool
from typing import Dict, Optional

from components import Player, Market, TimeTrack, GameState, TurnAction


class EngineStrategy(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def calculate_turn(self, player1: Player, player2: Player, patches: Market, track: TimeTrack, max_depth: int) -> GameState:
        pass

    @abstractmethod
    def calculate_state(self, game_state: GameState, max_depth, current_depth) -> GameState:
        pass

    @staticmethod
    @abstractmethod
    def choose_winner(player: Player, opponent: Player, current_best: GameState, candidate: GameState):
        pass


class GreedySingleCoreStrategy(EngineStrategy):

    @property
    def name(self) -> str:
        return "greedy_single_core"

    def calculate_turn(self, player1: Player, player2: Player, patches: Market, track: TimeTrack, max_depth: int) -> GameState:
        game_state = GameState(player1, player2, patches, track)
        return self.calculate_state(game_state, max_depth, 0)

    def calculate_state(self, game_state: GameState, max_depth, current_depth) -> GameState:
        best: Optional[GameState] = None
        game_state.determine_active_player()

        for turn_action in TurnAction:
            if not game_state.turn_action_possible(turn_action):
                continue

            game_state_copy = copy.deepcopy(game_state)
            game_state_copy.execute_turn(turn_action)

            if current_depth < max_depth and not game_state_copy.game_end():
                contender = self.calculate_state(game_state_copy, max_depth, current_depth + 1)
                best = self.choose_winner(game_state.player, game_state.opponent, best, contender)
            else:
                best = self.choose_winner(game_state.player, game_state.opponent, best, game_state_copy)

        return best

    @staticmethod
    def choose_winner(player: Player, opponent, current_best: GameState, candidate: GameState):
        if not current_best:
            return candidate

        current_outcome = current_best.history[-1]
        candidate_outcome = candidate.history[-1]

        return candidate if candidate_outcome[player.player_number] > candidate_outcome[opponent.player_number] \
                            and candidate_outcome[player.player_number] > current_outcome[player.player_number] else current_best


class GreedyFourCoreStrategy(GreedySingleCoreStrategy):

    @property
    def name(self) -> str:
        return "greedy_four_core"

    def calculate_turn(self, player1: Player, player2: Player, patches: Market, track: TimeTrack, max_depth: int) -> GameState:
        pool = Pool(4)
        game_state = GameState(player1, player2, patches, track)

        args = []
        for turn_action in TurnAction:
            if not game_state.turn_action_possible(turn_action):
                continue

            game_state_copy = copy.deepcopy(game_state)
            game_state_copy.execute_turn(turn_action)

            if not game_state_copy.game_end():
                args.append((game_state_copy, max_depth, 1))

        game_states = pool.starmap(self.calculate_state, args)

        current_winner = game_states.pop()
        for candidate in game_states:
            current_winner = self.choose_winner(current_winner.player, current_winner.opponent, current_winner, candidate)

        return current_winner


greedy_s = GreedySingleCoreStrategy()
greedy_f = GreedyFourCoreStrategy()

strategies: Dict[str, EngineStrategy] = {
    greedy_s.name.lower(): greedy_s,
    greedy_f.name.lower(): greedy_f,
}
