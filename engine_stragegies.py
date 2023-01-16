import copy
from abc import ABC, abstractmethod
from typing import Dict

from components import Player, Market, TimeTrack, GameState, TurnAction, NoopGameState, AbstractGameState


class EngineStrategy(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def calculate_turn(self, player1: Player, player2: Player, patches: Market, track: TimeTrack, max_depth: int) -> AbstractGameState:
        pass


class GreedyStrategy(EngineStrategy):

    @property
    def name(self) -> str:
        return "Greedy"

    def calculate_turn(self, player1: Player, player2: Player, patches: Market, track: TimeTrack, max_depth: int) -> AbstractGameState:
        game_state = GameState(player1, player2, patches, track)
        return self.__calculate_turn(game_state, max_depth, 0)

    def __calculate_turn(self, game_state: GameState, max_depth, current_depth) -> AbstractGameState:
        best: AbstractGameState = NoopGameState()

        # todo endgamehandling if there are no more patches
        for turn_action in TurnAction:
            game_state_copy = copy.deepcopy(game_state)
            # todo cut TurnAction for patch, if not enough buttons
            game_state_copy.execute_turn(turn_action)

            if current_depth < max_depth:
                contender = self.__calculate_turn(game_state_copy, max_depth, current_depth + 1)
                # todo determine winner but with regards to that the player wants to maximize his turn
            else:
                current_game_state_final_score_p1, current_game_state_final_score_p2 = best.get_final_score()
                candidate_game_state_final_score_p1, candidate_game_state_final_score_p2 = game_state_copy.get_final_score()
                best = game_state_copy if candidate_game_state_final_score_p1 > candidate_game_state_final_score_p2 and \
                                          candidate_game_state_final_score_p1 > current_game_state_final_score_p1 else best

        return best


greedy = GreedyStrategy()

strategies: Dict[str, EngineStrategy] = {
    greedy.name.lower(): greedy,
}
