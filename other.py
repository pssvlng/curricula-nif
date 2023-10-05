from collections import namedtuple
import json
import sys
import wn
from rdflib import Graph
from passivlingo_dictionary.Dictionary import Dictionary
from passivlingo_dictionary.models.SearchParam import SearchParam
from ContextWord import ContextWord
from WordnetWordBuilder import WordnetWordBuilder

def merge_graphs_from_files(base: str, range: int):
    graph = Graph()
    for i in range (0, range):    
        g = Graph()
        g.parse(f'{base}_{i}.ttl', format='ttl')
        graph += g

    output_file = f"{base}.ttl"    
    graph.serialize(destination=output_file, format="turtle", encoding='UTF-8')            

def create_synset_hash_links(lang: str, categories: list, depth: int):
    result = {}    
    WordTuple = namedtuple('MyWord', ['name', 'wordKey', 'lang', 'synonyms'])
    builder = WordnetWordBuilder()
    synsets = wn.synsets(lang=lang)
    cntr = 0
    for synset in synsets:
        wordKey = '.'.join([synset.lemmas()[0], synset.pos, synset.id.split('-')[1], synset.id.split('-')[0]])
        word = WordTuple(name=synset.lemmas()[0], wordKey=wordKey, lang=lang, synonyms=synset.lemmas()[1:])        
        category_list_words = builder.build(word, categories, depth)
        result[f'{lang}-{depth}-{synset.ili.id}'] = ', '.join(category_list_words)
        cntr += 1
        if cntr % 100 == 0:
            print(f'{cntr} results of {len(synsets)} processed')
    return result 


#Main Program
if len(sys.argv) == 3:
    lang = sys.argv[1]
    depth = int(sys.argv[2])    
    file_path = f"{lang}_{depth}.json"
    data = create_synset_hash_links(lang, ['hypernym', 'hyponym', 'meronym', 'holonym'], depth)
    with open(file_path, "w", encoding='utf-8') as json_file:    
        json.dump(data, json_file, ensure_ascii=False, indent=4)



