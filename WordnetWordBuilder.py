from passivlingo_dictionary.Dictionary import Dictionary
from passivlingo_dictionary.models.SearchParam import SearchParam

class WordnetWordBuilder:

    def __get_list(self, lang: str, wordKey: str, category, current_level: int, depth: int)-> list:
        if current_level > depth:
            return []

        dict = Dictionary()
        param = SearchParam()
        param.lang = lang
        param.filterLang = lang
        param.wordkey = wordKey
        param.category = category
        word_list = dict.findWords(param)    

        result = word_list
        for word in word_list:
            result.extend(self.__get_list(lang, word.wordKey, category, current_level + 1, depth))

        return result
        

    def build(self, word, categories: list, depth: int) -> list:
        result = []        
        for category in categories:
            result.extend(self.__get_list(word.lang, word.wordKey, category, 0, depth))
        
        return [item for sublist in [x.synonyms for x in result] for item in sublist] + word.synonyms + [word.name]

    def __repr__(self):
        return 'WordnetWordBuilder()'

    def __str__(self):
        return 'WordnetWordBuilder()'
