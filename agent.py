import sys

from observer import Observer
from card import Cards, CardSet
from log import Log

class Agent:
    def __init__(self, player, names):
        self.player = player
        self.names = names
        self.name = names[player]
        self.observer = Observer(names)
        self.cards = []

    def start_round(self, card):
        self.observer.start_round(self.player, card)
        self.cards = [card]

    def report_draw(self, card):
        self.observer.report_draw(self.player, card)
        self.cards.append(card)

    def report_play(self, *k, **kw):
        self.observer.report_play(*k, **kw)
        player = kw['player']
        card = kw['card']
        target = kw.get('target', None)
        discard = kw.get('discard', None)
        new_card = kw.get('new_card', None)
        other_card = kw.get('other_card', None)
        loser = kw.get('loser', None)

        if self.player == player:
            self.cards.remove(card)

        if card == Cards.BARON and self.player == loser:
            self.cards.remove(discard)
        elif card == Cards.PRINCE and self.player == target:
            self.cards.remove(discard)
            self.cards.append(new_card)
        elif card == Cards.KING and self.player in (player, target):
            del self.cards[0]
            self.cards.append(other_card)

class LowballAgent(Agent):
    def __init__(self, player, names):
        super(LowballAgent, self).__init__(player, names)

    def _most_likely(self, exclude_card=None):
        player = None
        card = None
        certainty = 0
        fallback = None
        for p in self.observer.players:
            if p.out or p.number == self.player:
                continue

            (c, cert) = p.cards.most_likely(exclude_card)
            if fallback is None:
                fallback = (p.number, c, cert)

            if p.handmaiden:
                continue

            if cert > certainty:
                player = p.number
                card = c
                certainty = cert

        if player:
            return (player, card, certainty)
        else:
            return fallback

    def _least_likely(self, exclude_card=None):
        player = None
        card = None
        certainty = 10
        fallback = None
        for p in self.observer.players:
            if p.out or p.number == self.player:
                continue

            (c, cert) = p.cards.most_likely(exclude_card)

            if fallback is None:
                fallback = (p.number, c, cert)

            if p.handmaiden:
                continue

            if cert < certainty:
                player = p.number
                card = c
                certainty = cert

        if player:
            return (player, card, certainty)
        else:
            return fallback

    def _most_likely_less_than(self, card):
        player = None
        certainty = 0
        fallback = None
        for p in self.observer.players:
            if p.out or p.number == self.player:
                continue

            cert = p.cards.chance_less_than(card)

            if fallback is None:
                fallback = (p.number, cert)

            if p.handmaiden:
                continue

            if cert > certainty:
                player = p.number
                certainty = cert

        if player:
            return (player, certainty)
        else:
            return fallback

    def _highest_expected_value(self):
        player = None
        value = 0
        fallback = None
        for p in self.observer.players:
            if p.out or p.number == self.player:
                continue

            v = p.cards.expected_value()

            if fallback is None:
                fallback = (p.number, v)

            if p.handmaiden:
                continue

            if v > value:
                player = p.number
                value = v

        if player:
            return (player, value)
        else:
            return fallback

    def _get_required_play(self):
        if Cards.COUNTESS in self.cards:
            if Cards.PRINCE in self.cards or Cards.KING in self.cards:
                return {'card': Cards.COUNTESS}
        return None

    def get_play(self):
        Log.print('ai: %s play options: %s %s' % (self.name, Cards.name(self.cards[0]), Cards.name(self.cards[1])))
        self.observer.print_state('ai')
        ret = self._get_required_play()
        if not ret:
            for card in range(Cards.NUM_CARDS):
                if card in self.cards:
                    other = self.cards[0] if self.cards[1] == card else self.cards[1]
                    ret = {'card': card}
                    if card == Cards.GUARD:
                        (player, card, certainty) = self._most_likely(exclude_card=Cards.GUARD)
                        ret['target'] = player
                        ret['challenge'] = card
                        Log.print('ai: %s has %i%% chance of card %s' % (self.names[player], certainty * 100, Cards.name(card)))
                    elif card == Cards.PRIEST:
                        (player, card, certainty) = self._least_likely()
                        ret['target'] = player
                        Log.print('ai: %s has %i%% chance of card %s' % (self.names[player], certainty * 100, Cards.name(card)))
                    elif card == Cards.BARON:
                        (player, certainty) = self._most_likely_less_than(other)
                        ret['target'] = player
                        Log.print('ai: %s has %i%% chance of being less than card %s' % (self.names[player], certainty * 100, Cards.name(other)))
                    elif card in (Cards.PRINCE, Cards.KING):
                        (player, value) = self._highest_expected_value()
                        ret['target'] = player
                        Log.print('ai: %s has highest expected value: %f' % (self.names[player], value))
                    break
        return ret

class ConsoleAgent(Agent):
    def __init__(self, player, names):
        super(ConsoleAgent, self).__init__(player, names)

    def start_round(self, card):
        super(ConsoleAgent, self).start_round(card)
        print('%s starts with card %s' % (self.name, Cards.name(card)))
        self.discarded = []
        for card in range(Cards.NUM_CARDS):
            self.discarded.append(0)

    def report_draw(self, card):
        super(ConsoleAgent, self).report_draw(card)
        print('%s draws card %s' % (self.name, Cards.name(card)))

    def report_play(self, *k, **kw):
        super(ConsoleAgent, self).report_play(*k, **kw)

        player = kw['player']
        card = kw['card']
        self.discarded[card] += 1
        target = kw.get('target', None)
        discard = kw.get('discard', None)
        if target is not None:
            print('%s plays card %s on %s' %(self.names[player], Cards.name(card), self.names[target]))
        else:
            print('%s plays card %s' % (self.names[player], Cards.name(card)))

        if discard:
            self.discarded[discard] += 1

        if card == Cards.GUARD:
            challenge = kw['challenge']
            print('%s is accused of having card %s' % (self.names[target], Cards.name(challenge)))
            if discard:
                print('%s discards card %s' % (self.names[target], Cards.name(discard)))
                print('%s is out' % self.names[target])
            else:
                print('%s does not have card %s' % (self.names[target], Cards.name(challenge)))
        elif card == Cards.PRIEST:
            other_card = kw.get('other_card', None)
            if other_card:
                print('%s has card %s' % (self.names[target], Cards.name(other_card)))
        elif card == Cards.BARON:
            loser = kw.get('loser', None)
            if loser is not None:
                print('%s loses challenge, discards card %s' % (self.names[loser], Cards.name(discard)))
                print('%s is out' % self.names[loser])
                other_card = kw.get('other_card', None)
                if other_card:
                    print('Winning card was %s' % Cards.name(other_card))
        elif card == Cards.PRINCE:
            print('%s discards card %s' % (self.names[target], Cards.name(discard)))
            if discard == Cards.PRINCESS:
                print('%s is out' % self.names[target])
            new_card = kw.get('new_card', None)
            if new_card:
                print('%s draws new card %s' % (self.names[target], Cards.name(new_card)))
        elif card == Cards.KING:
            other_card = kw.get('other_card', None)
            if other_card:
                print('%s now has card %s' % (self.names[target], Cards.name(other_card)))
        elif card == Cards.PRINCESS:
            print('%s is out' % self.names[player])
        print()

    def get_play(self):
        card = None

        self.cards = sorted(self.cards)
        play = {}
        while card is None:
            s = '  '.join([player.name for player in self.observer.players if not player.out])
            print('Players still in round: %s' % s)
            s = '  '.join('%s(%i)' % (Cards.name(card), self.discarded[card]) for card in range(Cards.NUM_CARDS) if self.discarded[card] > 0)
            print('Discarded cards: %s' % s)
            print('Available cards are [%i] %s  [%i] %s' % (self.cards[0], Cards.name(self.cards[0]), self.cards[1], Cards.name(self.cards[1])))
            print('Enter selection:')
            line = sys.stdin.readline().strip()
            if line.startswith('enable'):
                Log.enable(line.split(' ')[1])
                continue
            elif line.startswith('disable'):
                Log.disable(line.split(' ')[1])
                continue

            c = int(line)
            if c not in self.cards:
                print('Invalid selection')
                continue

            card = c
            play['card'] = card

        if card in (Cards.GUARD, Cards.PRIEST, Cards.BARON, Cards.PRINCE, Cards.KING):
            players = []
            for player in self.observer.players:
                if player.out:
                    continue

                if player.number == self.player and card != Cards.PRINCE:
                    continue

                players.append(player)

            s = '  '.join(['[%i] %s' % (player.number + 1, player.name) for player in players])
            print('Players: %s' % s)
            print('Enter target player:')
            s = int(sys.stdin.readline())
            if s < len(self.observer.players) + 1:
                play['target'] = s - 1

        if card == Cards.GUARD:
            s = '  '.join(['[%i] %s' % (card, Cards.name(card)) for card in range(Cards.GUARD, Cards.NUM_CARDS)])
            print('Cards: %s' % s)
            print('Enter challenge card:')
            c = int(sys.stdin.readline())
            play['challenge'] = c

        return play
