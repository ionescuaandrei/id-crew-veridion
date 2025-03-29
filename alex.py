import requests
from time import sleep
import random

host = "172.18.4.158:8000"
post_url = f"{host}/submit-word"
get_url = f"{host}/get-word"
status_url = f"{host}/status"

NUM_ROUNDS = 5



def play_game(player_id):

    for round_id in range(1, NUM_ROUNDS+1):
        round_num = -1
        while round_num != round_id:
            response = requests.get(get_url)
            print(response.json())

            round_num = response.json()['round']

            sleep(1)

        if round_id > 1:
            status = requests.get(status_url)
            print(status.json())

        choosen_word = "Gamma-Ray Burst"
        data = {"player_id": player_id, "word_id": choosen_word, "round_id": round_id}
        response = requests.post(post_url, json=data)
        print(response.json())
