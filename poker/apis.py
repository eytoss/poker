"""poker third party apis
"""

import requests

hand_score_endpoint = "http://www.pokerbrain.net:88/hand/score"
player_score_endpoint = "http://www.pokerbrain.net:88/player/score"

def score_hands(hands_dict):
    """
    input a hand dict which represents 5 ~ 7 cards
    return the json obj which
    contains score and related info for it.

    post body looks like this:
{
   "players":[
      {
         "name":"player 1",
         "pocket":[
            {
               "suit":"h",
               "name":"a"
            },
            {
               "suit":"c",
               "name":"a"
            }
         ]
      },
      {
         "name":"player 2",
         "pocket":[
            {
               "suit":"c",
               "name":"7"
            },
            {
               "suit":"d",
               "name":"2"
            }
         ]
      }
   ],
   "community":[
      {
         "suit":"s",
         "name":"a"
      },
      {
         "suit":"s",
         "name":"k"
      },
      {
         "suit":"s",
         "name":"8"
      }
   ]
}    
    
    """
    response = requests.post(player_score_endpoint, params=hands_dict)
    return response.json()