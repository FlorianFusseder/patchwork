from typing import Dict

import click
from PIL import ImageColor
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait

from components import Market, Player, TimeTrack


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


def init_game(patches: Dict, token_position, players: Dict) -> (TimeTrack, Market, Player, Player):
    click.echo("Init data structure...")
    pieces = Market(patches, token_position)
    player1 = players.popitem()[1]
    player2 = players.popitem()[1]
    track = TimeTrack([player1, player2])
    p1 = Player(player1, track)
    p2 = Player(player2, track)
    return pieces, p1, p2


def print_statistics(player1, player2, statistics):
    def all_button_rates(player):
        return [bought_piece[1] for bought_piece in statistics[player.player_name]['chart']]

    def print_(player, other_player):
        if player.player_name in statistics and 'chart' in statistics[player.player_name]:
            click.secho(f"{player.player_name}'s ", fg=get_player_color(player), nl=False)
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


def get_player_color(player):
    return ImageColor.getcolor(f"#{player.color_code}", "RGB")


def print_game_status(p1, p2):
    def get_color(p1_, p2_):
        if p1_.score > p2_.score:
            return 'green'
        elif p1_.score < p2_.score:
            return 'red'
        else:
            return 'yellow'

    def print_(p1_, p2_):
        click.secho(f"{p1_.player_name}", fg=get_player_color(p1_), nl=False)
        click.echo("'s score: ", nl=False)
        click.secho(p1_.score, bg=(get_color(p1_, p2_)), fg='black')

    print_(p1, p2)
    print_(p2, p1)
    click.echo()


def get_active_player(p1, p2):
    active_player: Player = p1 if p1.my_turn() else p2
    click.secho(f"{active_player.player_name}'s turn", fg=get_player_color(active_player), nl=False)
    click.echo(f" ({active_player.status()})\n")
    return active_player


def process_player_choice(turn, active_player, driver, results, statistics):
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
    if newly_bought:
        assert len(newly_bought) == 1, newly_bought
        bought_patch_id = newly_bought.pop()
        for i in range(3):
            result_dict = results[i]
            if result_dict['patch'].id_ == bought_patch_id:
                statistics \
                    .setdefault(active_player.player_name, {}) \
                    .setdefault("chart", []) \
                    .append((result_dict['patch'], result_dict['button-rate']))

                click.secho(f"{active_player.player_name} ", fg=get_player_color(active_player), nl=False)
                bought_best = results['winner-index'] == i
                click.secho(
                    f"bought {'optimal' if bought_best else 'suboptimal'} patch {i + 1} with button-rate: ",
                    fg=('green' if bought_best else 'yellow'), nl=False)
                click.secho(f"{result_dict['button-rate']:.2f}", bg=('green' if bought_best else 'yellow'), fg='black',
                            nl=False)
                if bought_best:
                    click.echo()
                else:
                    click.echo(" instead of ", nl=False)
                    click.secho(f"Patch {results['winner-index'] + 1} with button-rate: ", fg='green', nl=False)
                    click.secho(f"{results[results['winner-index']]['button-rate']:.2f}", bg='green', fg='black')
                break
    else:
        click.secho(f"{active_player.player_name}", fg=get_player_color(active_player), nl=False)
        click.echo(" traded buttons for time!")
    click.echo()


def print_suggestion(turn, results):
    winner_index = results['winner-index']
    candidates = []
    non_affordable = []
    low_button_rate = []

    def print_(lst):
        [click.echo(f"\tRate of {elem[0] + 1} => {elem[1]['button-rate']:.3f}\t({elem[1]['patch']})") for elem in
         lst]

    for i in range(3):
        patch = results[i]
        _list = None
        if patch['affordable'] and patch['button-rate'] > 1:
            _list = candidates
        elif patch['affordable'] and patch['button-rate'] <= 1:
            _list = low_button_rate
        elif not patch['affordable']:
            _list = non_affordable
        else:
            Exception(f"Patch not categorizable: {patch}")

        _list.append((i, patch))

    if candidates:
        candidates.sort(key=lambda x: x[1]['button-rate'], reverse=True)
        click.echo("Affordable:")
        print_(candidates)
    if non_affordable:
        click.echo("Omitted due to cost:")
        print_(non_affordable)
    if low_button_rate:
        click.echo("Omitted due to button-rate:")
        print_(low_button_rate)

    click.echo()

    if winner_index is not None:
        click.secho(f"Suggested patch (turn {turn}): ", nl=False, fg='green')

        match winner_index:
            case 0:
                winner_string = "1st"
            case 1:
                winner_string = "2nd"
            case 2:
                winner_string = "3rd"
            case _:
                raise ValueError("Winner index has to be 1, 2 or 3")

        click.secho(f"{winner_string} piece => rate: {results[winner_index]['button-rate']}",
                    nl=False, fg='green', bold=True, underline=True)
        click.secho(f" ({results[winner_index]['patch']})")
    else:
        click.secho("No valid candidate => advance", fg='red')


def print_delimiter(nl=False):
    click.echo("-" * 50)
    if nl:
        click.echo()


@click.command()
@click.argument("url")
def go_play(url):
    options = Options()
    options.add_argument('--headless')
    statistics = {}
    click.clear()
    with Firefox(options=options) as driver:
        click.echo(f"Starting Browser...")
        driver.start_client()
        click.echo(f"Trying to connect to {url}... (this takes a while)")
        driver.get(url)
        click.clear()
        while True:
            print_delimiter()
            turn, patches, token_position, players = read_game_state(driver)
            pieces, p1, p2 = init_game(patches, token_position, players)
            print_delimiter(True)
            active_player: Player = get_active_player(p1, p2)
            print_game_status(p1, p2)
            results = active_player.calculate_turn(pieces)
            print_suggestion(turn, results)
            process_player_choice(turn, active_player, driver, results, statistics)
            print_statistics(p1, p2, statistics)


if __name__ == "__main__":
    go_play()
