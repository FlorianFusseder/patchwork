import copy
from abc import ABC, abstractmethod
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
    def choose_winner(current_best: GameState, candidate: GameState):
        pass


class GreedyStrategy(EngineStrategy):

    @property
    def name(self) -> str:
        return "Greedy"

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
                best = self.choose_winner(best, contender)
            else:
                best = self.choose_winner(best, game_state_copy)

        return best

    @staticmethod
    def choose_winner(current_best: GameState, candidate: GameState):
        if not current_best:
            return candidate

        return candidate

        # if True:
        #     return candidate if candidate_game_state_final_score_p1 > candidate_game_state_final_score_p2 and \
        #                         candidate_game_state_final_score_p1 > current_game_state_final_score_p1 else current_best
        # else:
        #     return candidate if candidate_game_state_final_score_p1 < candidate_game_state_final_score_p2 < current_game_state_final_score_p2 else current_best


greedy = GreedyStrategy()

strategies: Dict[str, EngineStrategy] = {
    greedy.name.lower(): greedy,
}
