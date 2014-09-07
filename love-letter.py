import random
import dealer, agent

class Arena:
    def __init__(self, agents):
        self.agents = agents
        self.dealer = dealer.Dealer(agents)
        self.wins = []
        for agent in self.agents:
            self.wins.append(0)

    def run_games(self, num_games):
        for i in range(num_games):
            winner = self.dealer.do_game()
            self.wins[winner] += 1

        return self.wins

names = ['Player 1', 'Player 2', 'Player 3', 'Player 4']
agents = [agent.EndgameAgent(0, names), agent.LowballAgent(1, names), agent.LowballAgent(2, names), agent.LowballAgent(3, names)]
arena = Arena(agents)

num_games = 2000
wins = arena.run_games(num_games)
print('Final statistics:')
for i in range(len(agents)):
    print('%s (%s): %i (%i%%)' % (agents[i].name, agents[i].__class__.__name__, wins[i], wins[i] * 100 / num_games))
