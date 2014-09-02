import random
import dealer, agent

random.seed(1)
names = ['Player 1', 'Player 2', 'Player 3', 'Player 4']
agents = [agent.ConsoleAgent(0, names), agent.LowballAgent(1, names), agent.LowballAgent(2, names), agent.LowballAgent(3, names)]
dealer = dealer.Dealer(agents)
dealer.do_game()
