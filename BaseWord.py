from abc import abstractmethod, ABCMeta

class BaseWord:

    __metaclass__ = ABCMeta

    def __init__(self):
        self.name = ''
        self.pos = ''
        self.offset = ''
        self.wordKey = ''
        
    def __str__(self):
        return self.name
