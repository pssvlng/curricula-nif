
import json
import spacy
from nltk.corpus import wordnet as wn
from rdflib import Namespace
from bs4 import BeautifulSoup

nlp = {}
nlp['en'] = spacy.load('en_core_web_lg') 
nlp['de'] = spacy.load('de_core_news_lg')    

lexvo = {}
lexvo['en'] = 'http://www.lexvo.org/page/iso639-3/eng'
lexvo['de'] = 'http://www.lexvo.org/page/iso639-3/deu'

spotlight_url = {}
spotlight_url['de'] = 'https://wlo.yovisto.com/spotlight/annotate'
spotlight_url['en'] = 'https://wlo.yovisto.com/spotlight/annotate'

word_compare_lookup = {}
with open('de_0.json', "r") as json_file:
    word_compare_lookup['de_0'] = json.load(json_file)
with open('de_1.json', "r") as json_file:
    word_compare_lookup['de_1'] = json.load(json_file)      

nif = Namespace("http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#")
dbpedia = Namespace("http://dbpedia.org/resource/")
itsrdf = Namespace("http://www.w3.org/2005/11/its/rdf#")
curriculum_ns = Namespace("https://w3id.org/curriculum/")
ili_uri = "http://ili.globalwordnet.org/ili/"
ili_en_uri = "https://en-word.net/ttl/ili/"
olia_uri = "http://purl.org/olia/olia.owl#"
olia_ns = Namespace("http://purl.org/olia/olia.owl#")

def remove_html_tags_and_whitespace(input_string):
    soup = BeautifulSoup(input_string, 'html.parser')        
    clean_string = soup.get_text()        
    clean_string = clean_string.strip()    
    return clean_string

def merge_lists(entities, words):
    last_index = 0
    for entry in entities:
        to_search = entry[0].split(' ')
        search_surface = [word[0] for word in words[last_index:]]
        for index, _ in enumerate(search_surface):
            if entry[0] == ' '.join(search_surface[index:index + len(to_search)]):                    
                try:
                    last_index += index
                    whitespace = words[last_index + len(to_search) - 1][3]
                    words[last_index:last_index + len(to_search) - 1] = []
                    if last_index >= len(words):
                        words.append((entry[0], entry[1], entry[2], whitespace, entry[4]))
                    else:   
                        words[last_index] = (entry[0], entry[1], entry[2], whitespace, entry[4])                    
                    last_index += 1
                    break
                except Exception as e:
                    print(f"Error while processing Named Entities in Generic Tokenizer: {e}")
                    
    return words 

def tag_text(textToTag: str, lang = 'de'):
    result = []
    entities = []
    if not textToTag:
        return (result, entities)    
    try:        
        words = nlp[lang](textToTag)                                                    
        for word in [ent for ent in words.ents]:                        
            entities.append((word.text, "NOUN", word.lemma_, "", ""))
        
        for word in words:                        
            result.append((word.text, word.pos_, word.lemma_, word.whitespace_, ""))
        
    except Exception as e:
        print(f'Spacy Tagger failed on following text: {textToTag}: {e}')        
    
    return (result, entities)    

def getSpacyToWordnetPosMapping(pos):
        choices = {'VERB': 'v', 'NOUN': 'n',
                   'ADV': 'r', 'ADJ': 'a'}
        return choices.get(pos, 'x')

def add_unique_triple(g, subject, predicate, object):
    if (subject, predicate, object) not in g:
        g.add((subject, predicate, object))

    return g    