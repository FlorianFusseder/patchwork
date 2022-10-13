from typing import Dict, List

import click
from PIL import ImageColor
from bs4 import BeautifulSoup
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from components import Patches, Player, TimeTrack
from pieces import p_arrays


def get_owned_patches(soup: BeautifulSoup, color_code: str) -> List:
    pieces = soup.find("div", id=f"pieces_{color_code}").findChildren("div", class_="patch")
    return [p['id'] for p in pieces]


def get_soup(driver):
    element = driver.find_element(By.ID, "overall-content")
    html = element.get_attribute('outerHTML')
    soup = BeautifulSoup(html, "html.parser")
    return soup


def read_game(driver):
    print("Read data...")

    with click.progressbar(p_arrays.keys()) as indices:
        for id_ in indices:
            WebDriverWait(driver, 30).until(expected_conditions.presence_of_all_elements_located((By.ID, id_)))

    soup: BeautifulSoup = get_soup(driver)

    patches = dict()
    token = soup.find("div", id="token_neutral")

    patches_html = soup.find('div', id='market')
    for elem in patches_html.findChildren("div", class_="patch"):
        assert elem['id'].startswith("patch_")
        title_: [str] = elem['title'].split()
        patches[elem['id']] = {
            'data-order': elem['data-order'],
            'button-cost': title_[2],
            'time-cost': title_[5],
            'income': title_[-1]
        }

    player_html = soup.find('div', id="player_boards")
    player = {}

    for player_board in player_html.findChildren("div", class_="player-board"):
        player_id = int(player_board["id"].split("_")[-1])
        current_player = player_html.findChild("div", id=f"avatar_active_wrap_{player_id}")['style']
        player_ref = player_board.findChild("a")
        player_name = player_ref.text
        player_color_code = player_ref["style"].split("#")[-1]

        time_counter = player_board.findChild("div", class_="time_counter mini_counter").text
        button_counter = player_board.findChild("div", class_="buttons_counter mini_counter").text
        income_counter = player_board.findChild("div", class_="income_counter subtext mini_counter").text
        empty_spaces_counter = player_board.findChild("div", class_="empties_counter mini_counter").text

        owned_patches = get_owned_patches(soup, player_color_code)

        player[player_id] = {
            "current_player": current_player == 'display: block;',
            "name": player_name,
            "time_counter": time_counter,
            "button_counter": button_counter,
            "income_counter": income_counter,
            "color_code": player_color_code,
            "empty_spaces": empty_spaces_counter,
            "owned_pieces": owned_patches
        }

    return patches, token['data-order'], player


class turn_ended(object):

    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        state_text: str = driver.find_element(*self.locator).text
        return not state_text.endswith("must take an action")


class turn_starts(object):

    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        state_text: str = driver.find_element(*self.locator).text
        return state_text.endswith("must take an action")


def init_game(patches: Dict, token_position: int, players: Dict) -> (TimeTrack, Patches, Player, Player):
    print("Init data structure...")
    pieces = Patches(patches, token_position)
    popitem = players.popitem()
    p1 = Player(popitem[0], popitem[1])
    popitem = players.popitem()
    p2 = Player(popitem[0], popitem[1])
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

    click.echo()
    print_(player1, player2)
    print_(player2, player1)
    click.echo("-" * 50)


def get_player_color(player):
    return ImageColor.getcolor(f"#{player.color_code}", "RGB")


def print_game_status(p1, p2):
    click.echo("-" * 50)
    click.echo()

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
    active_player: Player = p1 if p1.my_turn else p2
    click.secho(f"{active_player.player_name}'s turn", fg=get_player_color(active_player), nl=False)
    click.echo(f" ({active_player.status()})")
    return active_player


@click.command()
@click.argument("url")
def go_play(url):
    options = Options()
    options.add_argument('--headless')
    statistics = {}
    click.clear()
    with Firefox(options=options) as driver:
        print(f"Starting Browser...")
        driver.start_client()
        print(f"Trying to connect to {url}... (this takes a while)")
        driver.get(url)
        click.clear()
        while True:
            patches, token_position, players = read_game(driver)
            token_position = int(token_position)
            pieces, p1, p2 = init_game(patches, token_position, players)
            print_game_status(p1, p2)
            active_player: Player = get_active_player(p1, p2)
            patches_to_choose, winner_index, rates = active_player.calculate_turn(pieces)
            print("\n")
            if winner_index is not None:
                click.secho(f"Suggested patch: ", nl=False, fg='green')
                click.secho(f"{winner_index + 1} => rate: {rates[winner_index]}", nl=False, fg='green', bold=True,
                            underline=True)
                click.secho(f" ({patches_to_choose[winner_index]})")
            else:
                click.secho(f"Cannot afford any patches => advance", fg='red')
            before_owned_patches = active_player.owned_patches
            driver_wait = WebDriverWait(driver, 180)
            driver_wait.until(turn_ended((By.ID, 'pagemaintitletext')))
            driver_wait.until(turn_starts((By.ID, 'pagemaintitletext')))
            soup = get_soup(driver)
            current_owned_patches = get_owned_patches(soup, active_player.color_code)
            bought = (set(current_owned_patches) - set(before_owned_patches))
            click.clear()
            if bought:
                assert len(bought) == 1, print(bought)
                bought_patch_id = bought.pop()
                for i, patch in enumerate(patches_to_choose):
                    if patch.id_ == bought_patch_id:
                        statistics \
                            .setdefault(active_player.player_name, {}) \
                            .setdefault("chart", []) \
                            .append((patch, rates[i]))

                        click.secho(f"{active_player.player_name} ", fg=get_player_color(active_player), nl=False)
                        bought_best = winner_index == i
                        click.secho(
                            f"bought {'optimal' if bought_best else 'suboptimal'} patch {i + 1} with button_rate: ",
                            fg=('green' if bought_best else 'yellow'), nl=False)
                        click.secho(f"{rates[i]:.2f}", bg=('green' if bought_best else 'yellow'), fg='black', nl=False)
                        if bought_best:
                            click.echo()
                        else:
                            click.echo(" instead of ", nl=False)
                            click.secho(f"patch {winner_index + 1} with button_rate: ", fg='green', nl=False)
                            click.secho(f"{rates[winner_index]:.2f}", bg='green', fg='black')
                        break
            else:
                click.echo(f"{active_player.player_name} traded buttons for time!")

            print_statistics(p1, p2, statistics)


if __name__ == "__main__":
    go_play()
