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
