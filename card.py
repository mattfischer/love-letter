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
        try:
            return self.cards[card] / sum(self.cards)
        except ZeroDivisionError:
            return 0

    def most_likely(self, exclude):
        cards = range(Cards.NUM_CARDS)
        cards = sorted(cards, reverse=True)
        cards = sorted(cards, key=lambda x: self.cards[x], reverse=True)
        card = cards[0]
        if card == exclude:
            card = cards[1]

        return (card, self.certainty(card))

    def chance_less_than(self, card):
        try:
            count = sum(self.cards[c] for c in range(card))
            return count / sum(self.cards)
        except ZeroDivisionError:
            return 0

    def expected_value(self):
        try:
            count = sum(c * self.cards[c] for c in range(Cards.NUM_CARDS))
            return count / sum(self.cards)
        except ZeroDivisionError:
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
