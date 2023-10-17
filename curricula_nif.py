from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, XSD
import requests
from SPARQLWrapper import SPARQLWrapper, JSON
from ContextWord import ContextWord
from WeightedWord import WeightedWord
from SimilarityClassifier import SimilarityClassifier
from WordnetWordBuilder import WordnetWordBuilder
from passivlingo_dictionary.Dictionary import Dictionary
from passivlingo_dictionary.models.SearchParam import SearchParam

from shared import *

def add_nif_context(g, subject, alt_label, lang='de'):
    sub = URIRef(subject)                    
    add_unique_triple(g, sub, URIRef('http://www.w3.org/2004/02/skos/core#altLabel'), Literal(alt_label, lang=lang))
    
    context_uri = URIRef(f'{subject}_nif=context_char=0,{len(alt_label)}')
    add_unique_triple(g,context_uri, RDF.type, nif.Context)
    #add_unique_triple(g,context_uri, RDF.type, nif.OffsetBasedString)
    add_unique_triple(g,context_uri, nif.beginIndex, Literal(0, datatype=XSD.nonNegativeInteger))
    add_unique_triple(g,context_uri, nif.endIndex, Literal(len(alt_label), datatype=XSD.nonNegativeInteger))
    add_unique_triple(g,context_uri, nif.isString, Literal(alt_label, lang=lang))
    add_unique_triple(g,context_uri, nif.predLang, URIRef(lexvo[lang]))
    #add_unique_triple(g,context_uri, nif.referenceContext, sub)
    add_unique_triple(g,sub, curriculum_ns.hasAnnotationTarget, context_uri)
    add_unique_triple(g,context_uri, curriculum_ns.isAnnotationTargetOf, sub)

    return g

def add_dbpedia_annotations(g, subject, alt_label, lang='de'):                    
    text_to_annotate = alt_label
    context_uri = URIRef(f'{subject}_nif=context_char=0,{len(alt_label)}')

    headers = {
        "Accept": "application/json",
    }
    
    params = {
        "text": text_to_annotate,        
    }

    response = requests.get(spotlight_url[lang], params=params, headers=headers)
    
    if response.status_code == 200:
        data = response.json()        
        annotations = data.get("Resources", [])

        for _, annotation in enumerate(annotations, start=1):            
            surface_form = annotation.get("@surfaceForm", "")
            start_index = int(annotation.get("@offset", 0))
            end_index = start_index + len(surface_form)
            annotation_uri = URIRef(f'{subject}_a=dbpedia-spotlite_char={start_index},{end_index}')
            dbpedia_resource = URIRef(annotation.get("@URI", ""))
            
            add_unique_triple(g,annotation_uri, RDF.type, nif.Phrase)
            #add_unique_triple(g,annotation_uri, RDF.type, nif.OffsetBasedString)
            add_unique_triple(g,annotation_uri, nif.beginIndex, Literal(start_index, datatype=XSD.nonNegativeInteger))
            add_unique_triple(g,annotation_uri, nif.endIndex, Literal(end_index, datatype=XSD.nonNegativeInteger))
            add_unique_triple(g,annotation_uri, nif.anchorOf, Literal(surface_form))
            add_unique_triple(g,annotation_uri, nif.predLang, URIRef(lexvo[lang]))
            add_unique_triple(g,annotation_uri, nif.referenceContext, context_uri)
            add_unique_triple(g,annotation_uri, itsrdf.taAnnotatorsRef, URIRef('http://www.dbpedia-spotlight.com'))
            add_unique_triple(g,annotation_uri, itsrdf.taConfidence, Literal(annotation.get("@similarityScore", "0")))
            add_unique_triple(g,annotation_uri, itsrdf.taIdentRef, dbpedia_resource)
            #add_unique_triple(g,annotation_uri, curriculum_ns.isAnnotationTargetOf, context_uri)
            #add_unique_triple(g,context_uri, curriculum_ns.hasAnnotationTarget, annotation_uri)
        
        return g
    else:
        print(f"Error: {response.status_code} - {response.text}")

def add_wordnet_annotations(g, subject, alt_label, lang='de'):            
    exclusions = ['--',"'", "...", "…", "`", '"', '|', '-', '.', ':', '!', '?', ',', '%', '^', '(', ')', '$', '#', '@', '&', '*']
    context_uri = URIRef(f'{subject}_nif=context_char=0,{len(alt_label)}')

    tag_results = tag_text(alt_label, lang)
    wordTags = tag_results[0]
    dbpedia_entities = tag_results[1]                
    wordTags = merge_lists(dbpedia_entities, wordTags)        

    merge_results = []
    for t in wordTags:            
        word = ContextWord()            
        word.name = t[0]
        word.whitespace = t[3]            
        word.dbPediaUrl = t[4]            
        word.lang = lang
        if len([x for x in ["'", "...", "…", "`", '"', '|'] if x in t[0]]) <= 0 and t[1] in ['VERB', 'NOUN', 'ADV', 'ADJ']:                
            word.pos = getSpacyToWordnetPosMapping(t[1])                     
            word.lemma = t[2]

        merge_results.append(word)                  

    classifier = SimilarityClassifier(nlp[lang])      
    for index, value in enumerate(merge_results):         
        if value.lemma and value.pos and len(value.lemma) > 1 and value.lemma not in exclusions:   
            dict = Dictionary()
            param = SearchParam()    
            param.lang = lang
            param.woi = value.lemma
            param.lemma = value.lemma
            param.pos = value.pos
            param.filterLang = lang    
            words = dict.findWords(param);

            weighted_words = []
            
            for word in words:
                weighted_word = WeightedWord(word)
                words_to_compare = word_compare_lookup[f'{lang}_1'][f'{lang}-1-{word.ili}']                                         
                weighted_word.weight = classifier.classify(alt_label, words_to_compare)
                weighted_words.append(weighted_word)

            if len(weighted_words) > 0:                        
                selected_word = max(weighted_words, key=lambda obj: obj.weight).word    
                start_index = len(''.join([obj.name + obj.whitespace for obj in merge_results[:index]]))
                end_index = start_index + len(value.name)
                annotation_uri = URIRef(f'{subject}_a=spacy_char={start_index},{end_index}')
                ili = f'{ili_uri}{selected_word.ili}'
                ili_en = f'{ili_en_uri}{selected_word.ili}'
                olia_pos = f'{olia_uri}{selected_word.pos}'

                add_unique_triple(g,annotation_uri, RDF.type, nif.Phrase)
                #add_unique_triple(g,annotation_uri, RDF.type, nif.OffsetBasedString)
                add_unique_triple(g,annotation_uri, RDF.type, URIRef(olia_pos))        
                add_unique_triple(g,annotation_uri, nif.beginIndex, Literal(start_index, datatype=XSD.nonNegativeInteger))
                add_unique_triple(g,annotation_uri, nif.endIndex, Literal(end_index, datatype=XSD.nonNegativeInteger))
                add_unique_triple(g,annotation_uri, nif.anchorOf, Literal(value.name))
                add_unique_triple(g,annotation_uri, nif.predLang, URIRef(lexvo[lang]))
                add_unique_triple(g,annotation_uri, nif.referenceContext, context_uri)                                       
                add_unique_triple(g,annotation_uri, itsrdf.taAnnotatorsRef, URIRef('https://spacy.io'))
                add_unique_triple(g,annotation_uri, itsrdf.taIdentRef, URIRef(ili))
                add_unique_triple(g,annotation_uri, itsrdf.taIdentRef, URIRef(ili_en))
                #add_unique_triple(g,annotation_uri, curriculum_ns.isAnnotationTargetOf, context_uri)
                #add_unique_triple(g,context_uri, curriculum_ns.hasAnnotationTarget, annotation_uri)

    return g             

def get_nif_literals_curriculum():        
    #nlp.max_length = 3000000
                         
    sparql = SPARQLWrapper("https://edu.yovisto.com/sparql")
    sparql_queries = [
    """
    select distinct * where {
                 ?s a <https://w3id.org/curriculum/CompetenceItem>  .
                 ?s <http://www.w3.org/2004/02/skos/core#prefLabel>  ?l .             
             }                                               
             
    """,
    """
    select distinct * where {
                 ?s a <https://w3id.org/curriculum/FederalState>  .
                 ?s <http://www.w3.org/2004/02/skos/core#prefLabel>  ?l .                  
             }       
                                                     
    """,
    """
    select distinct * where {                                  
                ?s a <https://w3id.org/dini/dini-ns/Curriculum>  .
                ?s <http://www.w3.org/2004/02/skos/core#prefLabel>  ?l .           
             }       
                                                     
    """
    ]

    graph = Graph()
    for query in sparql_queries:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()    
        
        cntr = 0
        for result in results["results"]["bindings"]:
            subject = result["s"]["value"]                
            obj_prefLabel = result["l"]["value"]                            
            text = remove_html_tags_and_whitespace(obj_prefLabel)
            if text:
                add_nif_context(graph, subject, text)
                add_dbpedia_annotations(graph, subject, text)
                add_wordnet_annotations(graph, subject, text)
            cntr +=1
            if (cntr % 100 == 0):                                                
                print(f'{cntr} results of {len(results["results"]["bindings"])} processed')

    return graph    

#Main Program
graph = get_nif_literals_curriculum()            
output_file = "curricula_nif.ttl"
graph.serialize(destination=output_file, format="turtle", encoding='UTF-8')            

