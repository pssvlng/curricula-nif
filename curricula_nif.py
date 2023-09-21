import json
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, SKOS, XSD, DCTERMS
from typing import Optional, List, Tuple
import requests
from rdflib.plugins.sparql import prepareQuery
from SPARQLWrapper import SPARQLWrapper, JSON
from bs4 import BeautifulSoup
from functools import reduce
import spacy
from nltk.corpus import wordnet as wn
from ContextWord import ContextWord
from WeightedWord import WeightedWord
from SimilarityClassifier import SimilarityClassifier
from WordnetWordBuilder import WordnetWordBuilder
from passivlingo_dictionary.Dictionary import Dictionary
from passivlingo_dictionary.models.SearchParam import SearchParam

nlp = spacy.load('de_core_news_lg')    
#nlp.add_pipe('dbpedia_spotlight', config={'confidence': 0.99}, last=True)

spotlight_url = 'https://wlo.yovisto.com/spotlight/annotate'

nif = Namespace("http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#")
dbpedia = Namespace("http://dbpedia.org/resource/")
itsrdf = Namespace("http://www.w3.org/2005/11/its/rdf#")
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

def tag_text(textToTag: str):
    result = []
    entities = []
    if not textToTag:
        return (result, entities)    
    try:        
        words = nlp(textToTag)                                                    
        for word in [ent for ent in words.ents]:                        
            entities.append((word.text, "NOUN", word.lemma_, "", ""))
        
        for word in words:                        
            result.append((word.text, word.pos_, word.lemma_, word.whitespace_, ""))
        
    except Exception as e:
        print(f'Spacy Tagger failed on following text: {textToTag}: {e}')        
    
    return (result, entities)    

def getSpacyToWordnetPosMapping(pos):
        choices = {'VERB': wn.VERB, 'NOUN': wn.NOUN,
                   'ADV': wn.ADV, 'ADJ': wn.ADJ}
        return choices.get(pos, 'x')

def add_unique_triple(g, subject, predicate, object):
    if (subject, predicate, object) not in g:
        g.add((subject, predicate, object))

    return g    

def add_nif_context(g, subject, alt_label):
    sub = URIRef(subject)                    
    add_unique_triple(g, sub, URIRef('http://www.w3.org/2004/02/skos/core#altLabel'), Literal(alt_label, lang='de'))
    
    context_uri = URIRef(f'{subject}?nif=context&char=0,{len(alt_label)}')
    add_unique_triple(g,context_uri, RDF.type, nif.Context)
    add_unique_triple(g,context_uri, RDF.type, nif.OffsetBasedString)
    add_unique_triple(g,context_uri, nif.beginIndex, Literal(0, datatype=XSD.nonNegativeInteger))
    add_unique_triple(g,context_uri, nif.endIndex, Literal(len(alt_label), datatype=XSD.nonNegativeInteger))
    add_unique_triple(g,context_uri, nif.isString, Literal(alt_label, lang='de'))
    add_unique_triple(g,context_uri, nif.predLang, URIRef('http://www.lexvo.org/page/iso639-3/deu'))
    add_unique_triple(g,context_uri, nif.referenceContext, sub)
    add_unique_triple(g,sub, DCTERMS.isPartOf, context_uri)

    return g

def add_dbpedia_annotations(g, subject, alt_label):                    
    text_to_annotate = alt_label
    context_uri = URIRef(f'{subject}?nif=context&char=0,{len(alt_label)}')

    headers = {
        "Accept": "application/json",
    }
    
    params = {
        "text": text_to_annotate,
    }

    response = requests.get(spotlight_url, params=params, headers=headers)
    
    if response.status_code == 200:
        data = response.json()        
        annotations = data.get("Resources", [])

        for idx, annotation in enumerate(annotations, start=1):            
            surface_form = annotation.get("@surfaceForm", "")
            start_index = int(annotation.get("@offset", 0))
            end_index = start_index + len(surface_form)
            annotation_uri = URIRef(f'{subject}?a=dbpedia-spotlite&char={start_index},{end_index}')
            dbpedia_resource = URIRef(annotation.get("@URI", ""))
            
            add_unique_triple(g,annotation_uri, RDF.type, nif.Phrase)
            add_unique_triple(g,annotation_uri, RDF.type, nif.OffsetBasedString)
            add_unique_triple(g,annotation_uri, nif.beginIndex, Literal(start_index, datatype=XSD.nonNegativeInteger))
            add_unique_triple(g,annotation_uri, nif.endIndex, Literal(end_index, datatype=XSD.nonNegativeInteger))
            add_unique_triple(g,annotation_uri, nif.anchorOf, Literal(surface_form))
            add_unique_triple(g,annotation_uri, nif.predLang, URIRef('http://www.lexvo.org/page/iso639-3/deu'))
            add_unique_triple(g,annotation_uri, nif.referenceContext, context_uri)
            add_unique_triple(g,annotation_uri, itsrdf.taAnnotatorsRef, URIRef('http://www.dbpedia-spotlight.com'))
            add_unique_triple(g,annotation_uri, itsrdf.taConfidence, Literal(annotation.get("@similarityScore", "0")))
            add_unique_triple(g,annotation_uri, itsrdf.taIdentRef, dbpedia_resource)
        
        return g
    else:
        print(f"Error: {response.status_code} - {response.text}")

def add_wordnet_annotations(g, subject, alt_label):            
    context_uri = URIRef(f'{subject}?nif=context&char=0,{len(alt_label)}')

    tag_results = tag_text(alt_label)
    wordTags = tag_results[0]
    dbpedia_entities = tag_results[1]                
    wordTags = merge_lists(dbpedia_entities, wordTags)        

    merge_results = []
    for t in wordTags:            
        word = ContextWord()            
        word.name = t[0]
        word.whitespace = t[3]            
        word.dbPediaUrl = t[4]            
        word.lang = 'de'
        if len([x for x in ["'", "...", "…", "`", '"'] if x in t[0]]) <= 0 and t[1] in ['VERB', 'NOUN', 'ADV', 'ADJ']:                
            word.pos = getSpacyToWordnetPosMapping(t[1])                     
            word.lemma = t[2]

        merge_results.append(word)                  

    classifier = SimilarityClassifier(nlp)  
    builder = WordnetWordBuilder()  
    for index, value in enumerate(merge_results):         
        if value.lemma and value.pos:   
            dict = Dictionary()
            param = SearchParam()    
            param.lang = 'de'
            param.woi = value.lemma
            param.lemma = value.lemma
            param.pos = value.pos
            param.filterLang = 'de'    
            words = dict.findWords(param);

            weighted_words = []
            
            for word in words:
                weighted_word = WeightedWord(word)
                words_to_compare = builder.build(word, ['hypernym', 'hyponym', 'meronym', 'holonym'], 0)
                weighted_word.weight = classifier.classify(alt_label, ' '.join(words_to_compare))
                weighted_words.append(weighted_word)

            if len(weighted_words) > 0:                        
                selected_word = max(weighted_words, key=lambda obj: obj.weight).word    
                start_index = len(''.join([obj.name + obj.whitespace for obj in merge_results[:index]]))
                end_index = start_index + len(value.name)
                annotation_uri = URIRef(f'{subject}?a=spacy&char={start_index},{end_index}')
                ili = f'{ili_uri}{selected_word.ili}'
                ili_en = f'{ili_en_uri}{selected_word.ili}'
                olia_pos = f'{olia_uri}{selected_word.pos}'

                add_unique_triple(g,annotation_uri, RDF.type, nif.Phrase)
                add_unique_triple(g,annotation_uri, RDF.type, nif.OffsetBasedString)
                add_unique_triple(g,annotation_uri, RDF.type, URIRef(olia_pos))        
                add_unique_triple(g,annotation_uri, nif.beginIndex, Literal(start_index, datatype=XSD.nonNegativeInteger))
                add_unique_triple(g,annotation_uri, nif.endIndex, Literal(end_index, datatype=XSD.nonNegativeInteger))
                add_unique_triple(g,annotation_uri, nif.anchorOf, Literal(value.name))
                add_unique_triple(g,annotation_uri, nif.predLang, URIRef('http://www.lexvo.org/page/iso639-3/deu'))
                add_unique_triple(g,annotation_uri, nif.referenceContext, context_uri)                                       
                add_unique_triple(g,annotation_uri, itsrdf.taAnnotatorsRef, URIRef('https://spacy.io'))
                add_unique_triple(g,annotation_uri, itsrdf.taIdentRef, URIRef(ili))
                add_unique_triple(g,annotation_uri, itsrdf.taIdentRef, URIRef(ili_en))

    return g        

def get_nif_literals():        
    #nlp.max_length = 3000000
                         
    sparql = SPARQLWrapper("https://edu.yovisto.com/sparql")
    sparql_query = """
    select distinct * where {
                 ?s a <https://w3id.org/curriculum/CompetenceItem>  .
                 ?s <http://www.w3.org/2004/02/skos/core#prefLabel>  ?l .
                 optional {?s <http://purl.org/dc/terms/description>  ?d .} 
             }                                               
    """
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)

    results = sparql.query().convert()    
    graph = Graph()
    cntr = 0
    for result in results["results"]["bindings"]:
        subject = result["s"]["value"]                
        obj_prefLabel = result["l"]["value"]                
        #obj_description = result["d"]["value"]
        text = remove_html_tags_and_whitespace(obj_prefLabel)
        if text:
            add_nif_context(graph, subject, text)
            add_dbpedia_annotations(graph, subject, text)
            add_wordnet_annotations(graph, subject, text)
        cntr +=1
        if (cntr % 100 == 0):                                                
            print(f'{cntr} results of {len(results["results"]["bindings"])} processed')
        
    output_file = "curricula_nif.ttl"
    graph.serialize(destination=output_file, format="turtle", encoding='UTF-8')            

get_nif_literals()            
