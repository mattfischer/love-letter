import random

from log import Log
from card import Cards

class Deck:
    def __init__(self):
        self.reset()

    def reset(self):
        self.cards = []
        for card in range(Cards.GUARD, Cards.NUM_CARDS):
            self.cards.extend([card for i in range(Cards.start_count(card))])
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop()

    def remaining(self):
        return len(self.cards)

class AgentInfo:
    def __init__(self, number, agent):
        self.cards = []
        self.out = False
        self.score = 0
        self.handmaiden = False
        self.agent = agent

class Dealer:
    def __init__(self, agents):
        self.agents = agents
        self.deck = Deck()
        self.agent_info = [AgentInfo(i, agent) for (i, agent) in enumerate(self.agents)]

    def _validate_play(self, play, player):
        if 'card' not in play:
            return False
        card = play['card']

        if card not in self.agent_info[player].cards:
            return False

        if card in (Cards.GUARD, Cards.PRIEST, Cards.BARON, Cards.PRINCE, Cards.KING):
            if 'target' not in play:
                return False
            target = play['target']
            if target not in range(len(self.agents)) or self.agent_info[target].out:
                return False

            if card != Cards.PRINCE and target == player:
                return False

            if card == Cards.GUARD:
                if 'challenge' not in play:
                    return False
                if play['challenge'] not in range(Cards.GUARD, Cards.NUM_CARDS):
                    return False

        return True

    def _report_play(self, *k, **kw):
        player = kw['player']
        card = kw['card']
        target = kw.get('target', None)
        discard = kw.get('discard', None)

        Log.print('report: ')
        if target is not None:
            Log.print('report: %s plays card %s on %s' %(self.agents[player], Cards.name(card), self.agents[target]))
        else:
            Log.print('report: %s plays card %s' % (self.agents[player], Cards.name(card)))

        if target is not None:
            if self.agent_info[target].handmaiden:
                Log.print('report: %s is unaffected due to HANDMAIDEN' % self.agents[target])
            else:
                if card == Cards.GUARD:
                    challenge = kw['challenge']
                    Log.print('report: %s is accused of having card %s' % (self.agents[target], Cards.name(challenge)))
                    if discard:
                        Log.print('report: %s discards card %s' % (self.agents[target], Cards.name(discard)))
                        Log.print('report: %s is out' % self.agents[target])
                    else:
                        Log.print('report: %s does not have card %s' % (self.agents[target], Cards.name(challenge)))
                elif card == Cards.BARON:
                    loser = kw.get('loser', None)
                    if loser is not None:
                        Log.print('report: %s loses challenge, discards card %s' % (self.agents[loser], Cards.name(discard)))
                        Log.print('report: %s is out' % self.agents[loser])
                elif card == Cards.PRINCE:
                    Log.print('report: %s discards card %s' % (self.agents[target], Cards.name(discard)))
                    if discard == Cards.PRINCESS:
                        Log.print('report: %s is out' % self.agents[target])

        if card == Cards.PRINCESS:
            Log.print('report: %s is out' % self.agents[player])

    def _process_play(self, play, player):
        report = {}
        report_player = {}
        report_target = {}
        card = play['card']
        report['card'] = card
        report['player'] = player
        player_info = self.agent_info[player]
        player_info.handmaiden = False
        player_info.cards.remove(card)

        target = play.get('target', None)
        if target is not None:
            report['target'] = target
            target_info = self.agent_info[target]

            if not target_info.handmaiden:
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

        if card == Cards.HANDMAIDEN:
            player_info.handmaiden = True
        elif card == Cards.PRINCESS:
            player_info.out = True

        self._report_play(**report)

        for i in range(len(self.agents)):
            report_agent = {}
            report_agent.update(report)

            if i == player:
                report_agent.update(report_player)
            if target is not None and i == target:
                report_agent.update(report_target)

            self.agents[i].report_play(**report_agent)

    def do_round(self, start_player):
        self.deck.reset()
        for info in self.agent_info:
            card = self.deck.draw()
            Log.print('dealer: Dealing %s to %s' % (Cards.name(card), info.agent))
            info.cards = [card]
            info.out = False
            info.handmaiden = False
            info.agent.start_round(card)

        current = start_player
        Log.print('dealer: Round starts with %s' % self.agents[current].name)
        while self.deck.remaining() > 1:
            info = self.agent_info[current]
            if not info.out:
                card = self.deck.draw()
                Log.print('dealer: Dealing %s to %s' % (Cards.name(card), info.agent))
                info.cards.append(card)
                info.agent.report_draw(card)

                play = info.agent.get_play()
                if not self._validate_play(play, current):
                    Log.print('dealer: Invalid play %s' % play)
                    continue

                self._process_play(play, current)

            players_in = len([info for info in self.agent_info if not info.out])
            if players_in == 1:
                break

            current = (current + 1) % len(self.agents)

        cards = [None if info.out else info.cards[0] for info in self.agent_info]

        Log.print('report:')
        Log.print('report: Round is over')
        Log.print('report: Final cards:')
        for (i, card) in enumerate(cards):
            if card is not None:
                Log.print('report:   %s: %s' % (self.agents[i], Cards.name(card)))

        lst = [i for i in range(len(cards))]
        lst = sorted(lst, key=lambda x: cards[x] or 0)
        winner = None
        if cards[lst[-1]] == cards[lst[-2]]:
            Log.print('report: Tie: No winner')
        else:
            winner = lst[-1]
            Log.print('report: Winner: %s' % self.agents[winner])
            self.agent_info[winner].score += 1

        for agent in self.agents:
            agent.end_round(cards, winner)

        return winner

    def do_game(self):
        for info in self.agent_info:
            info.score = 0
        start_player = 0
        winner = None

        for agent in self.agents:
            agent.start_game()

        while True:
            winner = self.do_round(start_player)
            if winner is not None:
                start_player = winner
                if self.agent_info[winner].score == 4:
                    break

        for agent in self.agents:
            agent.end_game(winner)

        Log.print('report:')
        Log.print('report: Game is over')
        Log.print('report: Winner: %s' % self.agents[winner])

        return winner
