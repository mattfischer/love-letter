from card import Cards, CardSet
from log import Log

class Player:
    def __init__(self, number, name):
        self.number = number
        self.name = name
        self.cards = CardSet.full()
        self.next_card = None
        self.out = False
        self.handmaiden = False
        self.score = 0

    def __str__(self):
        return self.name

class Observer:
    def __init__(self, names):
        self.deck_set = CardSet.full()
        self.players = []
        for i in range(len(names)):
            self.players.append(Player(i, names[i]))

    def _discard(self, card, exclude_player=None):
        self.deck_set.remove(card)
        for player in self.players:
            if player != exclude_player:
                player.cards.remove(card)

    def start_round(self, player, card):
        for p in self.players:
            p.cards = CardSet.full()
        player = self.players[player]
        self._discard(card, player)
        player.cards.clear(card)

    def report_draw(self, player, card=None):
        player = self.players[player]
        player.next_card = CardSet(self.deck_set)
        if card:
            player.next_card.clear(exclude=card)
            self._discard(card)

    def report_play(self, *k, **kw):
        player = self.players[kw['player']]
        card = kw['card']
        target = kw.get('target', None)
        if target is not None:
            target = self.players[target]
        discard = kw.get('discard', None)

        if player.next_card is None:
            player.next_card = CardSet(self.deck_set)

        player.handmaiden = False

        if player.cards.contains(card):
            player.cards = player.next_card

        self._discard(card)

        if card == Cards.GUARD:
            challenge = kw['challenge']
            if discard:
                self._discard(discard)
                target.cards.clear()
                target.out = True
            else:
                target.cards[challenge] = 0
        elif card == Cards.PRIEST:
            if 'other_card' in kw:
                target.cards.clear(kw['other_card'])
        elif card == Cards.BARON:
            loser = kw.get('loser', None)
            if loser is not None:
                loser = self.players[loser]
                winner = player if target == loser else target
                self._discard(discard)
                loser.cards.clear()
                loser.out = True
                other_card = kw.get('other_card', None)
                if other_card:
                    winner.cards.clear(exclude=other_card)
                else:
                    winner.cards.clear(cards=range(Cards.GUARD, discard + 1))
        elif card == Cards.HANDMAIDEN:
            player.handmaiden = True
        elif card == Cards.PRINCE:
            self._discard(discard)
            if discard == Cards.PRINCESS:
                target.out = True
            else:
                target.cards = CardSet(self.deck_set)
                if 'new_card' in kw:
                    target.cards.clear(kw['new_card'])
        elif card == Cards.KING:
            player.cards, target.cards = target.cards, player.cards
        elif card == Cards.COUNTESS:
            player.cards.clear(cards=range(Cards.GUARD, Cards.PRINCE))
        elif card == Cards.PRINCESS:
            player.cards.clear()
            player.out = True

        player.next_card = None

    def end_round(self, cards, winner):
        if winner is not None:
            self.players[winner].score += 1

    def print_state(self, zone):
        Log.print('%s: Player scores: %s' % (zone, '  '.join(['%s: %i' % (player.name, player.score) for player in self.players])))
        Log.print('%s: Deck set: %s' % (zone, self.deck_set))
        for p in self.players:
            Log.print('%s: %s set: %s' % (zone, p, p.cards))
