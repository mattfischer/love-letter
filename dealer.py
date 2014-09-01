import random

from log import Log
from card import Cards

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

class AgentInfo:
	def __init__(self):
		self.cards = []
		self.out = False

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
            info = AgentInfo()
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
