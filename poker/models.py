import uuid
import random
from django.db import models

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
    DECK_52 = [
        "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9", "dT", "dJ", "dQ", "dK", "dA",
        "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "cT", "cJ", "cQ", "cK", "cA",
        "h2", "h3", "h4", "h5", "h6", "h7", "h8", "h9", "hT", "hJ", "hQ", "hK", "hA",
        "s2", "s3", "d4", "s5", "s6", "s7", "s8", "s9", "sT", "sJ", "sQ", "sK", "sA",
    ]

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
        max_length=125, blank=True,
        #TODO: better to introduce one more delimiter between two cards,
        #      to facilitate front-end.
        #      note to avoid using `-` cause that's valid character in guid.
        help_text=(
            "Keeping records of the pocket cards the game have dealt with, "
            "so the next card generated from the game should never be one of them:) "
            "we will limit X=3 players at most in a game for now, "
            "so the maximum of cards will be (36+1+2*2+1)*X-1 = 125. "
            "'|' will be used as delimiter between players and "
            "'$' will be used as delimiter between player guid and his/her pocket cards."
            "for example: <guid_1>$h3h4|<guid_2>$d3d4|<guid_3>$c3c4 "
            "represents a game of 3 players each having 2 pocket cards(of course!)."
        ),
    )
    community_cards = models.CharField(
        max_length=14, blank=True,
        help_text=(
            "Keeping records of the community cards(0 ~ 5 cards) the game have dealt with "
            "using | as the delimiter. "
            "so the next card generated from the game should never be one of them:) "
            "for example: 'h3|d4|c6|s7' "
            "represents 4 cards has been dealt as community card and "
            "the current status of a game is in stage of `turn` "
        ),
    )
    # TODO: record user's entered with guid. so no need to record in pocket_cards?
    #       also auto serve the initial card.
    players_entered = models.CharField(
        max_length=125, blank=True,
        help_text=(
            "Keeping records of the pocket cards the game have dealt with, "
            "so the next card generated from the game should never be one of them:) "
            "we will limit X=3 players at most in a game for now, "
            "so the maximum of characters will be (36+1+1+1)*X-1 = 125. "
            "'|' will be used as delimiter between players and "
            "'$' will be used as delimiter between player guid and his/her status."
            "for example: <guid_1>$h3h4|<guid_2>$d3d4|<guid_3>$c3c4 "
            "represents a game of 3 players each having 2 pocket cards(of course!)."
        ),
    )
    total_num_of_players = models.IntegerField(help_text="the total number of players who entered this game Initially.")
    # TODO: foreign key relationship to Player model in v2.
    player_to_action = models.CharField(
        max_length=36, blank=True,
        help_text=(
            "It's this player's turn to act. "
            "The game would pause it's status until this player took action."
        ),
    )
    betting_status = models.CharField(
        max_length=125, blank=True,
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
        choices=STAGE_CHOICES,
        help_text="the current stage of the game."
    )

    bets = models.CharField(
        max_length=1000, blank=True,
        help_text=("place holder once we feel comfortable with introducing bets and betting history.")
    )

    def record_action(self):
        """
        record the user action, and update the status of the game
        if applicable, push the game into next stage.
        """
        # TODO: need to update the game: cards, betting status etc.
        raise NotImplementedError

    def _is_next_stage_ready(self):
        """
        return True if game is ready to move into next stage
        for example, if the current betting round is over.
        NOTE: this method need to remain very efficient
            as it is supposed to be called very frequently.
        """
        return "N" not in self.betting_status

    def move_to_next_stage_if_ready(self):
        """
        game engine would push the game into next stage
        whether this means a round of dealing cards,
            or showdown, or whatever # TODO: supported in v2.
        returns the updated game.
        """
        # TODO: implement this bulk stuff~
        if not self._is_next_stage_ready():
            return self
        # corresponding action would be taken and
        # game would be updated
        if self.stage == GameStages.Initial:
            # serve pocket cards
            pass
        elif self.stage == GameStages.PocketDone:
            # serve flop cards
            pass
        elif self.stage == GameStages.FLopDone:
            # serve turn card
            # FrenchDeck.next_random_cards(2, exclude_cards=self.community_cards.append(self.pocket_cards))
            pass
        elif self.stage == GameStages.TurnDone:
            # serve river card
            pass
        elif self.stage == GameStages.RiverDone:
            # compare!
            return self

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
        # self.pocket_cards example: <guid_1>$h3h4|<guid_2>$d3d4|<guid_3>$c3c4
        pocket_cards_list = self.pocket_cards.split("|")
        for pocket_cards in pocket_cards_list:
            if pocket_cards.split("$")[0] == user_guid:
                return pocket_cards.split("$")[1]
        # should never reach here, this indicates an issue of the game.
        # TODO: raise error and/or log this in v2.
        return None

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
