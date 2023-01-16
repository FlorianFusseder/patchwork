from typing import Dict

import click
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait

import engine_stragegies
from components import Market, Player, TimeTrack, Patch, TurnAction, GameState, AbstractGameState


def wait_for_player_turn():
    def _predicate(driver):
        """Next turn ca start if next player has to start an action"""
        state_text = driver.find_element(By.ID, "pagemaintitletext").text
        return state_text.endswith("must take an action")

    return _predicate


def read_game_state(driver):
    click.echo("Read data...")
    WebDriverWait(driver, 30).until(wait_for_player_turn())

    game_data = driver.execute_script("return window.gameui.gamedatas;")

    players = game_data['players']
    for key, player in players.items():
        player['income'] = game_data['counters'][f"income_{player['color']}_counter"]['counter_value']
        player['empty_spaces'] = game_data['counters'][f"empties_{player['color']}_counter"]['counter_value']
        player['players_turn'] = (game_data['gamestate']['active_player'] == player['id'])
        player['buttons'] = sum(
            [1 for token in game_data['tokens'].values() if token['location'] == f"buttons_{player['color']}"])
        player['time_marker'] = {
            'location': int(game_data['tokens'][f'timemarker_{player["color"]}']['location'].split('_')[1]),
            'top': game_data['tokens'][f'timemarker_{player["color"]}']['state']
        }
        player['tile_special7x7'] = game_data['tokens']['tile_special7x7']['location'] == f"tableau_{player['color']}"
        player['owned_patches'] = {patch['key'] for patch in
                                   game_data['tokens'].values() if
                                   patch['location'].startswith(f"square_{player['color']}")}

    patches = {}
    for id_ in Market.patch_keys:
        patches[id_] = game_data['tokens'][id_] | game_data['token_types'][id_]

    turn = driver.find_element(By.ID, "move_nbr").text
    return int(turn), patches, game_data['tokens']['token_neutral']['state'], players


def init_game(patches: Dict, token_position, players: Dict) -> (Market, Player, Player, TimeTrack):
    click.echo("Init data structure...")
    pieces = Market(patches, token_position)
    player1 = players.popitem()[1]
    player2 = players.popitem()[1]
    track = TimeTrack([player1, player2])
    p1 = Player(player1)
    p2 = Player(player2)
    return pieces, p1, p2, track


def print_statistics(player1, player2, statistics):
    def all_button_rates(player):
        return [bought_piece[1] for bought_piece in statistics[player.player_name]['chart']]

    def print_(player, other_player):
        if player.player_name in statistics and 'chart' in statistics[player.player_name]:
            click.secho(f"{player.player_name}'s ", fg=player.get_player_color(), nl=False)
            click.echo("Ø button-rate: ", nl=False)
            p1_button_rates = all_button_rates(player)
            p1_avg = sum(p1_button_rates) / len(p1_button_rates)
            p2_avg = None
            if other_player.player_name in statistics and 'chart' in statistics[other_player.player_name]:
                p2_button_rates = all_button_rates(other_player)
                p2_avg = sum(p2_button_rates) / len(p2_button_rates)
            click.secho(f"{p1_avg:.2f}", bg=('green' if not p2_avg or p1_avg >= p2_avg else 'red'), fg='black',
                        nl=False)
            click.echo(f"\t(history: {', '.join([str(round(r, 2)) for r in p1_button_rates])})")

    print_(player1, player2)
    print_(player2, player1)
    click.echo()


def print_game_status(p1, p2, track):
    p1_score = p1.get_current_score(track)
    p2_score = p2.get_current_score(track)

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

    print_(p1, p1_score, p2_score)
    print_(p2, p2_score, p1_score)
    click.echo()


def get_active_player(p1, p2, track):
    active_player: Player
    non_active_player: Player

    if p1.my_turn(track):
        active_player = p1
        non_active_player = p2
    else:
        active_player = p2
        non_active_player = p1

    click.secho(f"{active_player.player_name}'s turn", fg=active_player.get_player_color(), nl=False)
    click.echo(f" ({active_player.status(track)})\n")
    return active_player, non_active_player


def wait_for_player_choice(turn, active_player, driver, calculated_game_state: AbstractGameState, market: Market):
    def wait_move_nbr_increase(current_turn):
        def _predicate(driver):
            turn_nbr_ = driver.find_element(By.ID, "move_nbr").text
            return int(turn_nbr_) == current_turn + 1

        return _predicate

    WebDriverWait(driver, 180).until(wait_move_nbr_increase(turn))
    WebDriverWait(driver, 180).until(wait_for_player_turn())

    data = driver.execute_script("return window.gameui.gamedatas;")
    current_owned_patches = {patch['key'] for patch in data['tokens'].values() if
                             patch['location'].startswith(f"square_{active_player.color_code}")}
    newly_bought = current_owned_patches - set(active_player.owned_patches) - Market.special_patch_keys

    click.clear()
    chosen_action: TurnAction
    if newly_bought:
        assert len(newly_bought) == 1, newly_bought
        bought_patch_id = newly_bought.pop()
        click.secho(f"{active_player.player_name} ", fg=active_player.get_player_color(), nl=False)
        taken = next((i, p) for i, p in enumerate(market.get_next_three()) if p.id_ == bought_patch_id)
        click.echo(f"bought patch: {taken}")
        chosen_action = TurnAction(taken[0])
    else:
        click.secho(f"{active_player.player_name}", fg=active_player.get_player_color(), nl=False)
        click.echo(" traded buttons for time!")
        chosen_action = TurnAction.ADVANCE

    click.secho(f"{active_player.player_name} ", fg=active_player.get_player_color(), nl=False)
    if chosen_action == calculated_game_state.get_recommended_turn_action():
        click.echo("choose wisely", fg='green')
    else:
        click.echo("choose poorly", fg='red')


def print_delimiter(nl=False):
    click.echo("-" * 50)
    if nl:
        click.echo()


@click.command()
@click.argument("url")
@click.option("--strategy", "-s", default="greedy", help="Turn calculation Algorithm", type=click.Choice(["greedy"], case_sensitive=False))
@click.option("--depth", "-d", default=3, help="Depth for movement calculation", type=int)
def go_play(url, strategy, depth):
    options = Options()
    options.add_argument('--headless')
    click.clear()
    with Firefox(options=options) as driver:
        click.echo(f"Using {strategy} algorithm with depth {depth}")
        strategy = engine_stragegies.strategies[strategy.lower()]
        click.echo(f"Starting Browser...")
        driver.start_client()
        click.echo(f"Trying to connect to {url}... (this takes a while)")
        driver.get(url)
        click.clear()
        while True:
            print_delimiter()
            turn, patches, token_position, players = read_game_state(driver)
            pieces, p1, p2, track = init_game(patches, token_position, players)
            print_delimiter(True)
            active_player: Player
            non_active_player: Player
            active_player, non_active_player = get_active_player(p1, p2, track)
            print_game_status(p1, p2, track)
            calculated_game_state: AbstractGameState = strategy.calculate_turn(p1, p2, pieces, track, depth)
            click.echo(f"Best Turn: {calculated_game_state.get_recommended_turn_action()}")
            wait_for_player_choice(turn, active_player, driver, calculated_game_state, pieces)


if __name__ == "__main__":
    go_play()
