from typing import Dict

from components import Patches, Player, TimeTrack


def read_game():
    print("Read data...")
    from selenium.webdriver import Firefox
    from selenium.webdriver.common.by import By
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.support import expected_conditions
    from selenium.webdriver.support.wait import WebDriverWait
    from bs4 import BeautifulSoup

    options = Options()
    options.add_argument('--headless')
    driver = Firefox(options=options)
    driver.get('https://boardgamearena.com/6/patchwork?table=307392525')

    ids = [
        "patch_1",
        "patch_2",
        "patch_3",
        "patch_4",
        "patch_5",
        "patch_6",
        "patch_7",
        "patch_8",
        "patch_9",
        "patch_10",
        "patch_11",
        "patch_12",
        "patch_13",
        "patch_14",
        "patch_15",
        "patch_16",
        "patch_17",
        "patch_18",
        "patch_19",
        "patch_20",
        "patch_21",
        "patch_22",
        "patch_23",
        "patch_24",
        "patch_25",
        "patch_26",
        "patch_27",
        "patch_28",
        "patch_29",
        "patch_30",
        "patch_31",
        "patch_32",
        "patch_33"
    ]

    for id_ in ids:
        WebDriverWait(driver, 30).until(expected_conditions.presence_of_all_elements_located((By.ID, id_)))

    element = driver.find_element(By.ID, "overall-content")
    html = element.get_attribute('outerHTML')

    soup = BeautifulSoup(html, "html.parser")

    patches = dict()
    token = soup.find("div", class_="token_neutral")

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

        player[player_id] = {
            "current_player": current_player == 'display: block;',
            "name": player_name,
            "time_counter": time_counter,
            "button_counter": button_counter,
            "income_counter": income_counter,
            "color_code": player_color_code,
        }

    driver.quit()
    return patches, token['data-order'], player


def init_game(patches: Dict, token_position: int, players: Dict) -> (TimeTrack, Patches, Player, Player):
    print("Init data structure...")
    pieces = Patches(patches, token_position)
    popitem = players.popitem()
    p1 = Player(popitem[0], popitem[1])
    popitem = players.popitem()
    p2 = Player(popitem[0], popitem[1])
    return pieces, p1, p2


def go_play():
    patches, token_position, players = read_game()
    pieces, p1, p2 = init_game(patches, int(token_position), players)
    active_player: Player = p1 if p1.player_turn else p2
    print(f"{active_player.player_name}'s turn ({active_player.status()})")
    best_piece, index = active_player.calculate_turn(pieces)
    print(f"Choose patch {index}: {best_piece}")


if __name__ == "__main__":
    go_play()
