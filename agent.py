import sys, random, time

from observer import Observer
from card import Cards, CardSet
from log import Log

class Agent:
    def __init__(self, player, names):
        self.player = player
        self.name = names[player]
        self.observer = Observer(names)
        self.cards = []

    def __str__(self):
        return self.name

    def start_game(self):
        self.observer.start_game()

    def start_round(self, card):
        self.observer.start_round(self.player, card)
        self.cards = [card]

    def report_draw(self, card):
        self.observer.report_draw(self.player, card)
        self.cards.append(card)

    def end_round(self, cards, winner):
        self.observer.end_round(cards, winner)

    def end_game(self, winner):
        pass

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

        if target is not None and not self.observer.players[target].handmaiden:
            if card == Cards.BARON and self.player == loser:
                self.cards.remove(discard)
            elif card == Cards.PRINCE and self.player == target:
                self.cards.remove(discard)
                self.cards.append(new_card)
            elif card == Cards.KING and self.player in (player, target):
                del self.cards[0]
                self.cards.append(other_card)

    def _get_required_play(self):
        if Cards.COUNTESS in self.cards:
            if Cards.PRINCE in self.cards or Cards.KING in self.cards:
                return {'card': Cards.COUNTESS}
        return None

class LowballAgent(Agent):
    def __init__(self, player, names):
        super(LowballAgent, self).__init__(player, names)

    def start_round(self, card):
        super(LowballAgent, self).start_round(card)
        Log.print('ai: %s starts with card %s' % (self.name, Cards.name(card)))

    def report_draw(self, card):
        super(LowballAgent, self).report_draw(card)
        Log.print('ai: %s draws card %s' % (self.name, Cards.name(card)))

    def report_play(self, *k, **kw):
        super(LowballAgent, self).report_play(*k, **kw)
        card = kw['card']
        player = kw['player']
        target = kw.get('target', None)

        if target and not self.observer.players[target].handmaiden:
            if player == self.player:
                if card == Cards.PRIEST:
                    Log.print('ai: %s has card %s' % (self.observer.players[target], Cards.name(kw['other_card'])))
                elif card == Cards.KING:
                    Log.print('ai: %s now has card %s' % (self.name, Cards.name(kw['other_card'])))
            elif target == self.player:
                if card == Cards.BARON and kw.get('loser', None) == self.player:
                    Log.print('ai: Winning card was %s' % Cards.name(kw['other_card']))
                elif card == Cards.PRINCE and kw['discard'] != Cards.PRINCESS:
                    Log.print('ai: %s draws card %s' % (self.name, Cards.name(kw['new_card'])))
                elif card == Cards.KING:
                    Log.print('ai: %s now has card %s' % (self.name, Cards.name(kw['other_card'])))

    def _most_likely(self, exclude_card=None):
        lst = []
        for player in self.observer.players:
            if player.number != self.player and not player.out:
                (card, certainty) = player.cards.most_likely(exclude_card)
                lst.append((player, card, certainty))

        random.shuffle(lst)
        lst = sorted(lst, key=lambda x: x[0].score, reverse=True)
        lst = sorted(lst, key=lambda x: x[2], reverse=True)
        lst = sorted(lst, key=lambda x: x[0].handmaiden)

        Log.print('ai: Hand probabilities:')
        for l in lst:
            Log.print('ai:   %s: %s (%i%% chance) %s' % (l[0].name, Cards.name(l[1]), l[2] * 100, '(HANDMAIDEN)' if l[0].handmaiden else ''))

        winner = lst[0]
        Log.print('ai: %s has most certain hand (%i%% chance of card %s)' % (winner[0].name, winner[2] * 100, Cards.name(winner[1])))
        return winner

    def _least_likely(self, exclude_card=None):
        lst = []
        for player in self.observer.players:
            if player.number != self.player and not player.out:
                (card, certainty) = player.cards.most_likely(exclude_card)
                lst.append((player, card, certainty))

        random.shuffle(lst)
        lst = sorted(lst, key=lambda x: x[0].score, reverse=True)
        lst = sorted(lst, key=lambda x: x[2])
        lst = sorted(lst, key=lambda x: x[0].handmaiden)

        Log.print('ai: Hand probabilities:')
        for l in lst:
            Log.print('ai:   %s: %s (%i%% chance) %s' % (l[0].name, Cards.name(l[1]), l[2] * 100, '(HANDMAIDEN)' if l[0].handmaiden else ''))

        winner = lst[0]
        Log.print('ai: %s has least certain hand (%i%% chance of card %s)' % (winner[0].name, winner[2] * 100, Cards.name(winner[1])))
        return winner

    def _most_likely_less_than(self, card):
        lst = []
        for player in self.observer.players:
            if player.number != self.player and not player.out:
                certainty = player.cards.chance_less_than(card)
                lst.append((player, certainty))

        random.shuffle(lst)
        lst = sorted(lst, key=lambda x: x[0].score, reverse=True)
        lst = sorted(lst, key=lambda x: x[1], reverse=True)
        lst = sorted(lst, key=lambda x: x[0].handmaiden)

        Log.print('ai: Probabilities that hand is less than %s:' % Cards.name(card))
        for l in lst:
            Log.print('ai:   %s: %i%% %s' % (l[0].name, l[1] * 100, '(HANDMAIDEN)' if l[0].handmaiden else ''))

        winner = lst[0]
        Log.print('ai: %s has best chance (%i%%)' % (winner[0].name, winner[1] * 100))
        return winner

    def _highest_expected_value(self):
        lst = []
        for player in self.observer.players:
            if player.number != self.player and not player.out:
                value = player.cards.expected_value()
                lst.append((player, value))

        random.shuffle(lst)
        lst = sorted(lst, key=lambda x: x[0].score, reverse=True)
        lst = sorted(lst, key=lambda x: x[1], reverse=True)
        lst = sorted(lst, key=lambda x: x[0].handmaiden)

        Log.print('ai: Expected hand values:')
        for l in lst:
            Log.print('ai:   %s: %f %s' % (l[0].name, l[1], '(HANDMAIDEN)' if l[0].handmaiden else ''))

        winner = lst[0]
        Log.print('ai: %s has highest expected hand value %f' % (winner[0].name, winner[1]))
        return winner

    def get_play(self):
        Log.print('ai: %s play options: %s %s' % (self.name, Cards.name(self.cards[0]), Cards.name(self.cards[1])))
        self.observer.print_state('ai', self.player)
        ret = self._get_required_play()
        if not ret:
            cards = sorted(self.cards)
            card = cards[0]
            other_card = cards[1]

            ret = {'card': card}
            if card == Cards.GUARD:
                (player, card, certainty) = self._most_likely(exclude_card=Cards.GUARD)
                if other_card == Cards.HANDMAIDEN and certainty < 1:
                    ret['card'] = Cards.HANDMAIDEN
                else:
                    ret['target'] = player.number
                    ret['challenge'] = card
            elif card == Cards.PRIEST:
                (player, card, certainty) = self._least_likely()
                if other_card == Cards.HANDMAIDEN:
                    ret['card'] = Cards.HANDMAIDEN
                else:
                    ret['target'] = player.number
            elif card == Cards.BARON:
                (player, certainty) = self._most_likely_less_than(other_card)
                if other_card == Cards.HANDMAIDEN and certainty < 1:
                    ret['card'] = Cards.HANDMAIDEN
                else:
                    ret['target'] = player.number
            elif card in (Cards.PRINCE, Cards.KING):
                (player, value) = self._highest_expected_value()
                ret['target'] = player.number

        return ret

class EndgameAgent(LowballAgent):
    def get_play(self):
        if self.observer.deck_size <= len(self.observer.players):
            if Cards.PRINCE in self.cards:
                other_card = self.cards[0] if self.cards[1] == Cards.PRINCE else self.cards[1]
                deck_value = self.observer.deck_set.expected_value()
                if deck_value > other_card and deck_value > Cards.PRINCE:
                    ret = {'card' : Cards.PRINCE, 'target' : self.player }
                    return ret
                else:
                    values = [(i, player.cards.expected_value()) for (i, player) in enumerate(self.observer.players)]
                    values = sorted(values, key=lambda x: x[1], reverse=True)
                    for (i, value) in values:
                        if self.observer.players[i].out or i == self.player:
                            continue
                        if value > deck_value:
                            ret = {'card' : Cards.PRINCE, 'target' : i}
                            return ret
            elif Cards.KING in self.cards:
                other_card = self.cards[0] if self.cards[1] == Cards.KING else self.cards[1]
                values = [(i, player.cards.expected_value()) for (i, player) in enumerate(self.observer.players)]
                values = sorted(values, key=lambda x: x[1], reverse=True)
                for (i, value) in values:
                    if self.observer.players[i].out or i == self.player:
                        continue
                    if value > other_card and value > Cards.KING:
                        ret = {'card' : Cards.KING, 'target' : i}
                        return ret

        return super(EndgameAgent, self).get_play()

class ConsoleAgent(Agent):
    def __init__(self, player, names):
        super(ConsoleAgent, self).__init__(player, names)
        Log.enable('report', stripped=True)

    def start_game(self):
        super(ConsoleAgent, self).start_game()
        self.first_round = True

    def start_round(self, card):
        super(ConsoleAgent, self).start_round(card)
        print()
        if not self.first_round:
            print('Press Enter to begin next round')
            sys.stdout.flush()
            sys.stdin.readline()

        self.first_round = False
        print('%s starts with card %s' % (self.name, Cards.name(card)))
        self.discarded = [0 for i in range(Cards.NUM_CARDS)]

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

        if discard:
            self.discarded[discard] += 1

        if target:
            if not self.observer.players[target].handmaiden:
                if card == Cards.PRIEST:
                    other_card = kw.get('other_card', None)
                    if other_card:
                        print('%s has card %s' % (self.observer.players[target], Cards.name(other_card)))
                elif card == Cards.BARON:
                    loser = kw.get('loser', None)
                    if loser is not None:
                        other_card = kw.get('other_card', None)
                        if other_card:
                            print('Winning card was %s' % Cards.name(other_card))
                elif card == Cards.PRINCE:
                    new_card = kw.get('new_card', None)
                    if new_card:
                        print('%s draws new card %s' % (self.observer.players[target], Cards.name(new_card)))
                elif card == Cards.KING:
                    other_card = kw.get('other_card', None)
                    if other_card:
                        print('%s now has card %s' % (self.observer.players[target], Cards.name(other_card)))
        time.sleep(1)

    def get_play(self):
        card = None

        self.cards = sorted(self.cards)
        play = {}

        print()
        s = '  '.join(['%s(%i)' % (player.name, player.score) for player in self.observer.players if not player.out])
        print('Players still in round: %s' % s)
        s = '  '.join('%s(%i)' % (Cards.name(card), self.discarded[card]) for card in range(Cards.NUM_CARDS) if self.discarded[card] > 0)
        print('Discarded cards: %s' % s)

        while card is None:
            print('Available cards are [%i] %s  [%i] %s' % (self.cards[0], Cards.name(self.cards[0]), self.cards[1], Cards.name(self.cards[1])))
            print('Enter selection: ', end='')
            sys.stdout.flush()

            line = sys.stdin.readline().strip()
            if line.startswith('enable'):
                Log.enable(line.split(' ')[1])
                continue
            elif line.startswith('disable'):
                Log.disable(line.split(' ')[1])
                continue

            try:
                c = int(line)
                if c in self.cards:
                   card = c
            except ValueError:
                pass

            if card is None:
                print('  Invalid selection')
            elif card in (Cards.PRINCE, Cards.KING) and Cards.COUNTESS in self.cards:
                print('  Must discard COUNTESS')
                card = None

        play['card'] = card

        if card in (Cards.GUARD, Cards.PRIEST, Cards.BARON, Cards.PRINCE, Cards.KING):
            players = []
            for player in self.observer.players:
                if player.out:
                    continue

                if player.number == self.player and card != Cards.PRINCE:
                    continue

                players.append(player)

            target = None
            while target is None:
                print()
                s = '  '.join(['[%i] %s' % (player.number + 1, player.name) for player in players])
                print('Players: %s' % s)
                print('Enter target player: ', end='')
                sys.stdout.flush()

                try:
                    t = int(sys.stdin.readline()) - 1
                    if t in range(len(self.observer.players)) and self.observer.players[t] in players:
                        target = t
                except IndexError:
                    pass
                except ValueError:
                    pass

                if target is None:
                    print('  Invalid selection')

            play['target'] = target

        if card == Cards.GUARD:
            challenge = None
            while challenge is None:
                print()
                s = '  '.join(['[%i] %s' % (card, Cards.name(card)) for card in range(Cards.GUARD, Cards.NUM_CARDS)])
                print('Cards: %s' % s)
                print('Enter challenge card: ', end='')
                sys.stdout.flush()

                try:
                    c = int(sys.stdin.readline())
                    if c in range(Cards.GUARD, Cards.NUM_CARDS):
                        challenge = c
                except ValueError:
                    pass

                if challenge is None:
                    print('  Invalid selection')

            play['challenge'] = challenge

        return play

class RandomAgent(Agent):
    def get_play(self):
        ret = self._get_required_play()
        if not ret:
            ret = {}
            cards = list(self.cards)
            if Cards.PRINCESS in cards:
                cards.remove(Cards.PRINCESS)
            card = random.choice(cards)
            ret['card'] = card

            if card in (Cards.GUARD, Cards.PRIEST, Cards.BARON, Cards.PRINCE, Cards.KING):
                players = [i for i in range(len(self.observer.players)) if not self.observer.players[i].out]
                if card != Cards.PRINCE:
                    players.remove(self.player)
                target = random.choice(players)
                ret['target'] = target

                if card == Cards.GUARD:
                    ret['challenge'] = random.choice(range(Cards.PRIEST, Cards.NUM_CARDS))
        return ret
