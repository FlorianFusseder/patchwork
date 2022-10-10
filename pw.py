from PIL import Image

from components import Pieces, Player, TimeTrack
import numpy as np


def init_game() -> (TimeTrack, Pieces, Player, Player):
    print("Init data structure...")
    pieces = Pieces()
    p1 = Player(1, "Sonja")
    p2 = Player(2, "Florian")
    track = TimeTrack(p1, p2)
    return track, pieces, p1, p2


def go_play():
    track, pieces, p1, p2 = init_game()
    print(pieces)
    turn_counter = 0
    while not track.done():
        active_player: Player = p1 if p1.player_token > p2.player_token else p2
        print(f"Turn {turn_counter}: Player {active_player}'s turn")
        piece, location = active_player.calculate_turn(pieces)
        pieces.remove_piece(piece)
        active_player.put_piece(piece, location)
        special_patch = track.advance_player(active_player, piece)
        if special_patch:
            active_player.calculate_bonus_turn()
        turn_counter += 1


if __name__ == "__main__":
    pieces = Pieces()
    print(len(pieces))
    pieces[1].show()
    print(pieces)
