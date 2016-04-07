"""poker third party apis
"""

import requests

hand_score_endpoint = "http://www.pokerbrain.net:88/hand/score"

def score_hand(hand_str):
    """
    input a hand string which represents 5 ~ 7 cards
    return the json obj which
    contains score and related info for it.
    """
    # http://www.pokerbrain.net:88/hand/score?h=d7|d13|d12|d10|s8|d2|h14
    request_url = "{}?{}".format(hand_score_endpoint, hand_str)
    response = requests.get(request_url)
    return response.json()