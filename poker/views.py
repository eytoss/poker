# -*- coding: utf-8 -*-
"""This module provides consumer the interface of a online poker game.

The consumer, for example, the website would be responsible for
actively checking the status of the game and refresh the game
if needed.

WARNING: cheating of the game is currently expected in every possible way
"""

from django.http import HttpResponse
from poker.models import Game, GameStages
from django.views.decorators.http import require_POST, require_GET
import json
import uuid

# helper funcs
def _json_response(response_values):
    """
    Returns a formatted HttpResponse in JSON
    response_values is a dictionary of values
    """
    return HttpResponse(json.dumps(response_values), content_type='application/json')

def _json_error_response(message="Unknown Error"):
    return _json_response({'type': 'Error', 'message': message})

def _json_success_response(message="Unknown Error"):
    return _json_response({'type': 'Success', 'message': message})

# TODO: still need to implement key function list:
#    1. game ending: scoring best hands.

@require_GET
def game_status(request):
    """
    returns the current status. of a specific game,
        from the perspective of the given user if user_guid provided.
        so he can't see the pocket cards of others, of course :)
    Side Effects(updates) for this GET method:
        1. if no user specified, create user
        2. if no game specified, join or create game.
        3. pushes the game into the next stage if ready
    # TODO: remove side effects in v2.
    """
    user_guid = request.GET.get("user_guid", None)
    # TODO: in v2, create real User record.
    if not user_guid:
        user_guid = str(uuid.uuid4())
    # TODO: in v2 there should be rooms to choose from
    #       now just return the first non-over game.
    #       if there is no such game, create new one.
    game_guid = request.GET.get("game_guid", None)
    game = None
    if game_guid:
        try:
            # assume user is already in the game.
            # TODO: defensive coding in v2 to double check
            game = Game.objects.get(guid=game_guid)
        except:
            return _json_error_response("Invalid game guid.")
    else:
        # join the top game which has not started yet.
        games = Game.objects.filter(stage=GameStages.Initial)
        if games:
            game = games[0]
            game.total_num_of_players += 1
            game.player_guids += "|" + user_guid
        # if no such game, create new game.
        else:
            game = Game()
            game.total_num_of_players = 1
            game.player_guids = user_guid
            game.player_to_action = user_guid
        game.save()

    # here is where the game serving cards and compare hands.
    game = game.move_to_next_stage_if_ready()

    # construct game status.
    game_status = {}
    if user_guid:
        game_status["user_pocket_cards"] = game.get_user_pocket_cards(user_guid)
    game_status["community_cards"] = game.community_cards
    game_status["stage"] = game.stage
    # NOTE: front-end would ask user to act with action option list
    #       if user has matching user_guid
    game_status["player_to_action"] = game.player_to_action
    game_status["game_guid"] = str(game.guid)
    return _json_response(game_status)

@require_POST
def user_action(request):
    """
    Responsible for react to an action
        performed by a particular user
        from a particular game
    For example: 0. user join! 1. check. 2. fold. 3. call. 4. re-raise
    NOTE: for front-end, game_status is recommended to be called right after
          also note that scoring is currently being handled entirely in front-end.
          maybe let front-end tell me what the score is, and I compare them in the backend?
    """
    game_guid = request.POST.get("game_guid", None)
    user_guid = request.POST.get("user_guid", None)
    try:
        game = Game.objects.get(guid=game_guid)
    except:
        return _json_error_response("No such game.")
    action_type = request.POST.get("action_type", None)
    # TODO: log this in v2 as it indicates lack of restriction in front-end.
    if game.player_to_action != user_guid:
        return _json_error_response("Not your turn.")
    game.record_action(user_guid, action_type)
    return _json_success_response("Action completed.")
