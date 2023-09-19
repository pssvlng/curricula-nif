from .BaseWord import BaseWord

class ContextWord(BaseWord):           
    def __init__(self):
        super().__init__()                
        self.lemma = ''
        self.whitespace = ''
        self.dbPediaUrl = ''
        self.lang = 'en'
