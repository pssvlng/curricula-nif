import json
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, SKOS
from typing import Optional, List, Tuple
import requests
from rdflib.plugins.sparql import prepareQuery
from SPARQLWrapper import SPARQLWrapper, JSON
from bs4 import BeautifulSoup
from functools import reduce
import spacy

nlp = spacy.load('de_core_news_lg')    
nlp.add_pipe('dbpedia_spotlight', config={'confidence': 0.99}, last=True)        

def remove_html_tags_and_whitespace(input_string):
    soup = BeautifulSoup(input_string, 'html.parser')        
    clean_string = soup.get_text()        
    clean_string = clean_string.strip()    
    return clean_string

def merge_lists(dbpedia_entities, words):
    last_index = 0
    for entry in dbpedia_entities:
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
    dbpedia_entities = []
    if not textToTag:
        return (result, dbpedia_entities)    
    try:        
        words = nlp(textToTag)                                            
        if "dbpedia_spotlight" in self.nlp.pipe_names:
            for word in [ent for ent in words.ents if ent.label_ == 'DBPEDIA_ENT']:                        
                dbpedia_entities.append((word.text, "NOUN", word.lemma_, "", word._.dbpedia_raw_result['@URI']))
        
        for word in words:                        
            result.append((word.text, word.pos_, word.lemma_, word.whitespace_, ""))
        
    except:
        print(f'Spacy Tagger failed on following text: {textToTag}')        
    
    return (result, dbpedia_entities)    

def get_nif_literals():    
    nif = Namespace("http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#")
    sparql = SPARQLWrapper("https://edu.yovisto.com/sparql")
    sparql_query = """
    select distinct * where {
                 ?s a <https://w3id.org/curriculum/CompetenceItem>  .
                 ?s <http://www.w3.org/2004/02/skos/core#prefLabel>  ?l .
                 optional {?s <http://purl.org/dc/terms/description>  ?d .} 
             } 
             LIMIT 2
    """
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)

    results = sparql.query().convert()    
    graph = Graph()
    for result in results["results"]["bindings"]:
        subject = result["s"]["value"]        
        obj_prefLabel = result["l"]["value"]
        #obj_description = result["d"]["value"]
        text = remove_html_tags_and_whitespace(obj_prefLabel)
        tag_results = tag_text(text)
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
                word.pos = CommonHelper.getSpacyToWordnetPosMapping(t[1])                     
                word.lemma = t[2]

            merge_results.append(word)      
        
        alt_label = ''.join([obj.name + obj.whitespace for obj in merge_results])
        sub = URIRef(subject)                
        graph.add((sub, URIRef('http://www.w3.org/2004/02/skos/core#altLabel'), Literal(alt_label)))

        sub = URIRef(f'{subject}#char=0,{len(alt_label)}')
        graph.add((sub, nif.isString, Literal(alt_label)))
        graph.add((sub, nif.referenceContext, URIRef(subject)))

        # for index, value in enumerate(merge_results):            
        #     if rs.dbPediaUrl:
        #         start_index = len(''.join([obj.name + obj.whitespace for obj in merge_results[:index - 1]]))
        #         end_index = start_index + len(value.name)

    output_file = "nif.rdf"
    graph.serialize(destination=output_file, format="xml")            

get_nif_literals()            
