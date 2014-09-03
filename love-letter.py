import random
import dealer, agent

class Bullpen:
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

random.seed(1)
names = ['Player 1', 'Player 2', 'Player 3', 'Player 4']
agents = [agent.LowballAgent(0, names), agent.LowballAgent(1, names), agent.LowballAgent(2, names), agent.LowballAgent(3, names)]
bullpen = Bullpen(agents)

num_games = 1000
wins = bullpen.run_games(num_games)
print('Final statistics:')
for i in range(len(agents)):
    print('%s: %i (%i%%)' % (agents[i].name, wins[i], wins[i] * 100 / num_games))
