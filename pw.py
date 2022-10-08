class Location:
    pass


def go_play():
    board, pieces, p1, p2 = init_game()
    turn_counter = 0
    while not board.done():
        active_player: Player = board.determine_active_player(p1, p2)
        print(f"Turn {turn_counter}: Player {active_player}'s turn")
        piece, location = active_player.choose_piece(pieces)
        pieces.remove_piece(piece)
        active_player.put_piece(piece, location)
        board.advance_player(active_player, piece)
        turn_counter += 1


class Piece:
    pass


class Pieces:
    def remove_piece(self, piece):
        pass


class Player:
    def __init__(self, player_number: int, player_name: str):
        self.player_name = player_name
        self.player_number = player_number

    def __str__(self) -> str:
        return f"{self.player_number}"

    def choose_piece(self, pieces) -> (Piece, Location):
        return Piece(), Location()

    def put_piece(self, piece, location):
        pass


class GameBoard:

    def done(self):
        return False

    def determine_active_player(self, p1, p2) -> Player:
        return Player(0)

    def advance_player(self, active_player, piece):
        pass


def init_game() -> (GameBoard, Pieces, Player, Player):
    print("Init data structure...")
    board = GameBoard()
    pieces = Pieces()
    p1 = Player(1, "Sonja")
    p2 = Player(2, "Florian")
    return board, pieces, p1, p2


if __name__ == "__main__":
    go_play()
