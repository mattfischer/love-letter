import sys, random

class Cards:
    GUARD = 1
    PRIEST = 2
    BARON = 3
    HANDMAIDEN = 4
    PRINCE = 5
    KING = 6
    COUNTESS = 7
    PRINCESS = 8
    NUM_CARDS = 9

    names = [
        'NONE',
        'GUARD',
        'PRIEST',
        'BARON',
        'HANDMAIDEN',
        'PRINCE',
        'KING',
        'COUNTESS',
        'PRINCESS'
        ]

    @staticmethod
    def start_count(card):
        if card == Cards.GUARD:
            return 5
        elif card in range(Cards.PRIEST, Cards.KING):
            return 2
        elif card in range(Cards.KING, Cards.NUM_CARDS):
            return 1
        else:
            return 0

    @staticmethod
    def name(card):
         return Cards.names[card]

class CardSet:
    def __init__(self, other=None):
        if other:
            self.cards = other.cards[:]
        else:
            self.cards = []
            for i in range(Cards.NUM_CARDS):
                self.cards.append(0)

    def __getitem__(self, key):
        return self.cards[key]

    def __setitem__(self, key, val):
        self.cards[key] = val

    def __str__(self):
        ret = ''
        for i in range(Cards.NUM_CARDS):
            if self.cards[i] > 0:
                ret += '%s:%s ' % (Cards.name(i), self.cards[i])
        return ret

    def contains(self, card):
        return self.cards[card] > 0

    def clear(self, exclude=None, cards=range(Cards.NUM_CARDS)):
        for i in cards:
            if i != exclude:
                self.cards[i] = 0

    def remove(self, card):
        if self.cards[card] > 0:
            self.cards[card] -= 1

    def certainty(self, card):
        total = sum(self.cards)
        if total:
            return self.cards[card] / total
        else:
            return 0

    def most_likely(self, exclude):
        card = None
        certainty = 0
        for c in reversed(range(Cards.NUM_CARDS)):
            if c == exclude:
                continue

            cert = self.certainty(c)
            if cert > certainty:
                card = c
                certainty = cert
        return (card, certainty)

    def chance_less_than(self, card):
        total = sum(self.cards)
        if total:
            count = 0
            for c in range(Cards.GUARD, card):
                count += self.cards[c]
            return count / total
        else:
            return 0

    def expected_value(self):
        total = sum(self.cards)
        if total:
            count = 0
            for c in range(Cards.NUM_CARDS):
                count += c * self.cards[c]
            return count / total
        else:
            return 0

    @staticmethod
    def full():
        card_set = CardSet()
        for card in range(Cards.NUM_CARDS):
            card_set[card] = Cards.start_count(card)
        return card_set

    @staticmethod
    def single(card):
        card_set = CardSet()
        card_set[card] = Cards.start_count(card)
        return card_set

class Player:
    def __init__(self, number, name):
        self.number = number
        self.name = name
        self.cards = CardSet.full()
        self.next_card = None
        self.out = False
        self.handmaiden = False

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

    def print_state(self, zone):
        Log.print('%s: Deck set: %s' % (zone, self.deck_set))
        for p in self.players:
            Log.print('%s: %s set: %s' % (zone, p, p.cards))

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

        play = {}
        while card is None:
            s = '  '.join('%s(%i)' % (Cards.name(card), self.discarded[card]) for card in range(Cards.NUM_CARDS) if self.discarded[card] > 0)
            print('Discarded cards: %s' % s)
            print('Available cards are [1] %s  [2] %s' % (Cards.name(self.cards[0]), Cards.name(self.cards[1])))
            print('Enter selection:')
            line = sys.stdin.readline().strip()
            if line.startswith('enable'):
                Log.enable(line.split(' ')[1])
                continue
            elif line.startswith('disable'):
                Log.disable(line.split(' ')[1])
                continue

            c = int(line)
            if c in (1, 2):
                card = self.cards[c - 1]
            else:
                print('Invalid selection')
            play['card'] = card

        if card in (Cards.GUARD, Cards.PRIEST, Cards.BARON, Cards.PRINCE, Cards.KING):
            s = '  '.join(['[%i] %s' % (player.number + 1, player.name) for player in self.observer.players if not player.out and player.number != self.player])
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

class Deck:
    def __init__(self):
        self.reset()

    def reset(self):
        self.cards = []
        for card in range(Cards.GUARD, Cards.NUM_CARDS):
            for i in range(Cards.start_count(card)):
                self.cards.append(card)
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop()

    def remaining(self):
        return len(self.cards)

class Dealer:
    def __init__(self, agents):
        self.agents = agents
        self.deck = Deck()
        self.agent_info = []

    def _process_play(self, play, player):
        report = {}
        report_player = {}
        report_target = {}
        card = play['card']
        report['card'] = card
        report['player'] = player
        self.agent_info[player].cards.remove(card)
        player_info = self.agent_info[player]

        target = play.get('target', None)
        if target is not None:
            report['target'] = target
            target_info = self.agent_info[target]

        if card == Cards.GUARD:
            challenge = play['challenge']
            report['challenge'] = challenge

            if challenge in target_info.cards:
                report['discard'] = challenge
                target_info.cards.remove(challenge)
                target_info.out = True
        elif card == Cards.PRIEST:
            report_player['other_card'] = target_info.cards[0]
        elif card == Cards.BARON:
            player_card = player_info.cards[0]
            target_card = target_info.cards[0]
            if target_card > player_card:
                report['loser'] = player
                report['discard'] = player_card
                report_player['other_card'] = target_card
                player_info.cards.remove(player_card)
                player_info.out = True
            elif target_card < player_card:
                report['loser'] = target
                report['discard'] = target_card
                report_target['other_card'] = player_card
                target_info.cards.remove(target_card)
                target_info.out = True
        elif card == Cards.PRINCE:
            discard = target_info.cards[0]
            report['discard'] = discard
            target_info.cards.remove(discard)
            if discard == Cards.PRINCESS:
                target_info.out = True
            else:
                new_card = self.deck.draw()
                Log.print('dealer: Dealing %s to %s' % (Cards.name(card), self.agents[target].name))
                report_target['new_card'] = new_card
                target_info.cards.append(new_card)
        elif card == Cards.KING:
            report_player['other_card'] = target_info.cards[0]
            report_target['other_card'] = player_info.cards[0]
            target_info.cards, player_info.cards = player_info.cards, target_info.cards
        elif card == Cards.PRINCESS:
            player_info.out = True

        report_player.update(report)
        report_target.update(report)
        for i in range(len(self.agents)):
            if i == player:
                self.agents[i].report_play(**report_player)
            elif target is not None and i == target:
                self.agents[i].report_play(**report_target)
            else:
                self.agents[i].report_play(**report)

    def do_round(self):
        self.deck.reset()
        self.agent_info = []
        for agent in self.agents:
            card = self.deck.draw()
            Log.print('dealer: Dealing %s to %s' % (Cards.name(card), agent.name))
            class AgentInfo:
                pass
            info = AgentInfo()
            info.out = False
            info.cards = [card]
            self.agent_info.append(info)
            agent.start_round(card)

        current = 0
        while self.deck.remaining() > 1:
            if not self.agent_info[current].out:
                card = self.deck.draw()
                Log.print('dealer: Dealing %s to %s' % (Cards.name(card), agent.name))
                self.agent_info[current].cards.append(card)
                self.agents[current].report_draw(card)

                play = self.agents[current].get_play()
                self._process_play(play, current)

            players_in = 0
            for info in self.agent_info:
                if info.out == False:
                    players_in += 1

            if players_in == 1:
                break

            current += 1
            if current >= len(self.agents):
                current = 0

        cards = []
        for info in self.agent_info:
            if info.out:
                cards.append(0)
            else:
                cards.append(info.cards[0])

        print('Final standings:')
        winner = 0
        for i in range(len(cards)):
            if cards[i] > 0:
                print('  %s: %s' % (self.agents[i].name, Cards.name(cards[i])))
                if cards[i] > cards[winner]:
                    winner = i

        print('Winner: %s' % self.agents[winner].name)

class Log:
    enabled_zones = set()

    @staticmethod
    def print(s):
        if ':' in s:
            zone = s.split(':')[0]
        else:
            zone = None

        if zone is None or zone in Log.enabled_zones:
            print('* %s' % s)

    def enable(zone):
        Log.enabled_zones.add(zone)

    def disable(zone):
        Log.enabled_zones.remove(zone)

random.seed(2)
names = ['Player 1', 'Player 2', 'Player 3', 'Player 4']
agents = [ConsoleAgent(0, names), LowballAgent(1, names), LowballAgent(2, names), LowballAgent(3, names)]
dealer = Dealer(agents)
dealer.do_round()
