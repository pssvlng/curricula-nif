from abc import abstractmethod, ABCMeta

class WeightedWord:

    __metaclass__ = ABCMeta

    def __init__(self, word):
        self.word = word
        self.weight = 0.0

    def __str__(self):
        return "WeightedWord()"