import uuid
import random
from django.db import models
from poker.apis import score_hand

class FrenchDeck:
    """
    represents a standard 52 card deck
        and it's related helper functions
        (mostly dealt/shuffle functions)
    """
    # https://en.wikipedia.org/wiki/Standard_52-card_deck
    # Suits:
    # d - diamond
    # c - club
    # h - heart
    # s - spade
    # Ranks:
    # 2-9 - do you really need explanation for these :)
    # T - 10
    # J - Jack
    # Q - Queen
    # K - King
    # A - Ace
    suits = ['d', 'c', 'h', 's']
    ranks = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    DECK_52 = [x+y for x in suits for y in ranks]
#     DECK_52 = [
#         "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9", "dT", "dJ", "dQ", "dK", "dA",
#         "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "cT", "cJ", "cQ", "cK", "cA",
#         "h2", "h3", "h4", "h5", "h6", "h7", "h8", "h9", "hT", "hJ", "hQ", "hK", "hA",
#         "s2", "s3", "d4", "s5", "s6", "s7", "s8", "s9", "sT", "sJ", "sQ", "sK", "sA",
#     ]

    def _next_random_card(self, exclude_cards=None):
        """
        Returns a random card from a FULL or Partial DECK_52.
        NOTE: it's the caller's responsibility to:
            1. check the validity of the card(especially when exclude_cards=None).
            For example: in our texas holdem game, club of King
            would be Invalid if there is already one club of King
            served as either a pocker card or community card,
            in which case, the caller would call this method again
            until one valid card has been generated.
            2. update the exclude_cards list in some way
            For example: update the game.community_cards
            so next time this method being called, exclude_cards
            would have one more value in it.
        """
        return random.choice([x for x in self.DECK_52 if x not in exclude_cards])

    def next_random_cards(self, number_of_cards=1, exclude_cards=None):
        """
        responsible for dealing with the next number_of_cards card(s)
        """
        next_cards = []
        for x in range(0, number_of_cards):
            next_card = self._random_card(exclude_cards)
            next_cards.append(next_card)
            exclude_cards.append(next_card)
        return next_cards

class BettingStatus:
    """user's current betting status in a game"""
    # TODO: introduce Wait_For_Start status in v2, probably change BettingStatus to UserStatus
    Fold = "F" # fold. quit the game.
    Bet = "B" # bet
    Call_Or_Check = "C" # matches the current bet
    # re-raise, require actions for another round
    # also this would update other betting status to `N`
    # unless it's `F`.
    Reraise = "R"
    NotDone = "N" # not done betting

class GameStages:
    """stages of a game"""
    Initial = "I" # no card has been dealt yet.
    PocketDone = "P" # pocket cards have been dealt
    FLopDone = "F" # flop cards have been dealt
    TurnDone = "T" # turn cards have been dealt
    RiverDone = "R" # river cards have been dealt
    GameOver = "O" # everyone looks at the winner, Jin.

class Game(models.Model):
    """
    Reprecents the CURRENT status of a poker game
    """
    guid = models.CharField(
        max_length=36, blank=True, unique=True, default=uuid.uuid4,
        help_text=(
            "Unique, externally-friendly identifier for a specific poker game"
        ),
    )
    pocket_cards = models.CharField(
        max_length=125, default="",
        help_text=(
            "Keeping records of the pocket cards the game have dealt with, "
            "so the next card generated from the game should never be one of them:) "
            "we will limit X=3 players at most in a game for now, "
            "so the maximum of cards will be (2+1+2+1)*X-1 = 17. "
            "'|' will be used as delimiter between two pocket cards and "
            "'$' will be used as delimiter between players. "
            "for example: h3|h4$d3|d4$c3|c4 "
            "represents 3 sets of pocket cards"
        ),
    )
    community_cards = models.CharField(
        max_length=14, default="",
        help_text=(
            "Keeping records of the community cards(0 ~ 5 cards) the game have dealt with "
            "using | as the delimiter. "
            "so the next card generated from the game should never be one of them:) "
            "for example: 'h3|d4|c6|s7' "
            "represents 4 cards has been dealt as community card and "
            "the current status of a game is in stage of `turn` "
        ),
    )
    total_num_of_players = models.IntegerField(default=0, help_text="the total number of players who entered this game Initially.")
    player_guids = models.CharField(
        max_length=110, default="",
        help_text=(
            "Keeping records of the pocket cards the game have dealt with, "
            "so the next card generated from the game should never be one of them:) "
            "we will limit X=3 players at most in a game for now, "
            "so the maximum of characters will be (36+1)*X-1 = 110. "
            "'|' will be used as delimiter between players "
            "for example: <guid_1>|<guid_2>|<guid_3> "
            "represents a game of 3 players"
        ),
    )
    # TODO: foreign key relationship to Player model in v2.
    player_to_action = models.CharField(
        max_length=36, default="",
        help_text=(
            "It's this player's turn to act. "
            "The game would pause it's status until this player took action."
        ),
    )
    betting_status = models.CharField(
        max_length=125, default="",
        help_text=(
            "It's the current round betting status for all the active users "
            "The game engine would use this info to determine if next stage "
            "is ready."
            "For example: FBCR means user 1 folded, user 2 bet, "
            "user 3 called and user 4 re-reraised, and this indicates the "
            "betting round is NOT over."
        ),
    )

    STAGE_CHOICES = [(getattr(GameStages, key), key) for key in GameStages.__dict__.keys() if not key.startswith("__")]
    stage = models.CharField(
        max_length=1,
        default=GameStages.Initial,
        choices=STAGE_CHOICES,
        help_text="the current stage of the game."
    )

    bets = models.CharField(
        max_length=1000, default="",
        help_text=("place holder once we feel comfortable with introducing bets and betting history.")
    )

    def _get_next_user_guid(self, current_user_guid):
        """get the user guid to the right of current player"""
        index = self._get_player_index(current_user_guid)
        user_guid_list = self.player_guids.split("|")
        return user_guid_list[(index+1)%len(user_guid_list)]

    def record_action(self, user_guid, action_type):
        """
        record the user action, and update the status of the game
        if applicable, push the game into next stage.
        """
        # update betting status
        user_index = self._get_player_index(user_guid)
        user_action_list = list(self.betting_status)
        user_action_list[user_index] = action_type
        self.betting_status = "".join(user_action_list)

        self.player_to_action = self._get_next_user_guid(user_guid)
        self.save()

    def _is_next_stage_ready(self):
        """
        return True if game is ready to move into next stage
        for example, if the current betting round is over.
        NOTE: this method need to remain very efficient
            as it is supposed to be called very frequently.
        """
        return "N" not in self.betting_status and \
                self.total_num_of_players > 1

    def _get_served_card_list(self):
        # TODO: test this.
        pocket_card_list = self.pocket_cards.replace("$", "|").split("|")
        community_card_list = self.community_cards.split("|")
        return pocket_card_list.extend(community_card_list)

    def _get_user_guid(self, index):
        player_guid_list = self.player_guids.split("|")
        return player_guid_list[index % len(player_guid_list)]

    def _get_player_index(self, user_guid):
        if user_guid not in self.player_guids:
            raise Exception
        return self.player_guids.split("|").index(user_guid)

    def move_to_next_stage_if_ready(self):
        """
        game engine would push the game into next stage
        whether this means a round of dealing cards,
            or showdown, or whatever # TODO: supported in v2.
        returns the updated game.
        """
        if not self._is_next_stage_ready():
            return self

        # corresponding action would be taken and
        # game would be updated
        if self.stage == GameStages.RiverDone:
            # River card has been served and the betting round is done.
            # time for scoring!
            # TODO: waiting to use advanced api Jon is working one
            # score each hand and return the winner
            score_hand("asdfasdf")
            return

        if self.stage == GameStages.Initial:
            # serve pocket cards
            num_of_cards = self.total_num_of_players * 2
            pocket_cards = FrenchDeck.next_random_cards(
                number_of_cards=num_of_cards, exclude_cards=None)
            p_cards = "|".join(pocket_cards) # 'sA|s7|dK|a7|h3|h5' for 3 players
            self.pocket_cards = "$".join(p_cards[i:i+5] for i in range(0, len(p_cards), 6)) # 'sA|s7$dK|a7$h3|h5'
            self.stage = GameStages.PocketDone
        elif self.stage == GameStages.PocketDone:
            # serve 3 flop cards
            flop_cards = FrenchDeck.next_random_cards(
                number_of_cards=3, exclude_cards=self._get_served_card_list())
            self.community_cards = "|".join(flop_cards) # 'sA|s7|h5'
            self.stage = GameStages.FLopDone
        elif self.stage == GameStages.FLopDone:
            # serve turn card
            turn_card = FrenchDeck.next_random_cards(
                number_of_cards=1, exclude_cards=self._get_served_card_list())
            self.community_cards += "|" + turn_card # 'sA|s7|h5|hK'
            self.stage = GameStages.TurnDone
        elif self.stage == GameStages.TurnDone:
            # serve river card
            river_card = FrenchDeck.next_random_cards(
                number_of_cards=1, exclude_cards=self._get_served_card_list())
            self.community_cards += "|" + river_card # 'sA|s7|h5|hK|dK'
            self.stage = GameStages.RiverDone
        # TODO: consider folded users in v2
        self.player_to_action = self._get_user_guid(0)
        self.betting_status = "N" * self.total_num_of_players
        self.save() # NOTE: this would trigger updates actively to subscribers through websocket

    def number_of_cards_needed(self):
        """number of cards needed for the game to move into NEXT stage."""
        if self.stage == GameStages.Initial:
            return self.total_num_of_players * 2
        if self.stage == GameStages.PocketDone:
            return 3
        if self.stage in (
            GameStages.FLopDone,
            GameStages.TurnDone
        ):
            return 1
        return 0

    def available_actions(self):
        """
        the available action list for self.player_to_action
        # TODO: let user do whatever for now, improve this in v2
        """
        raise NotImplementedError

    def get_user_pocket_cards(self, user_guid):
        """get the pocket cards for given user"""
        if self.stage == GameStages.Initial:
            return None

        player_guid_list = self.player_guids.split("|")
        if user_guid not in player_guid_list:
            return None

        index = player_guid_list.index(user_guid)
        pocket_cards_list = self.pocket_cards.split("$")
        return pocket_cards_list[index]

class User(models.Model):
    """
    # Records the meta data for a user(name, chips etc) and the current game the user is in, if any.
    """
    guid = models.CharField(
        max_length=36, blank=True, unique=True, default=uuid.uuid4,
        help_text=(
            "Unique, externally-friendly identifier for a specific user"
        ),
    )
    username = models.CharField(
        max_length=20,
        help_text=(
            "Username, for example: bruce lee"
        ),
    )
