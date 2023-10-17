from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, XSD, SDO
import requests
from SPARQLWrapper import SPARQLWrapper, JSON
from ContextWord import ContextWord
from WeightedWord import WeightedWord
from SimilarityClassifier import SimilarityClassifier
from passivlingo_dictionary.Dictionary import Dictionary
from passivlingo_dictionary.models.SearchParam import SearchParam
from langdetect import detect
from datetime import datetime as dt
from shared import *
import sys
from collections import defaultdict

def add_nif_context_wlo(g, subject, name, description, keyword, keyword_key, lang):
    sub = URIRef(subject)                       
    
    if name:
        context_uri = URIRef(f'{subject}_nif=context_p=name_char=0,{len(name)}')
        add_unique_triple(g,context_uri, RDF.type, nif.Context)
        #add_unique_triple(g,context_uri, RDF.type, nif.OffsetBasedString)
        add_unique_triple(g,context_uri, nif.beginIndex, Literal(0, datatype=XSD.nonNegativeInteger))
        add_unique_triple(g,context_uri, nif.endIndex, Literal(len(name), datatype=XSD.nonNegativeInteger))
        add_unique_triple(g,context_uri, nif.isString, Literal(name, lang=lang))
        add_unique_triple(g,context_uri, nif.predLang, URIRef(lexvo[lang]))
        #add_unique_triple(g,context_uri, nif.referenceContext, sub)
        add_unique_triple(g,context_uri, nif.wasConvertedFrom, SDO.name)    
        add_unique_triple(g,sub, curriculum_ns.hasAnnotationTarget, context_uri)
        add_unique_triple(g,context_uri, curriculum_ns.isAnnotationTargetOf, sub)

    if description:
        context_uri = URIRef(f'{subject}_nif=context_p=description_char=0,{len(description)}')
        add_unique_triple(g,context_uri, RDF.type, nif.Context)
        #add_unique_triple(g,context_uri, RDF.type, nif.OffsetBasedString)
        add_unique_triple(g,context_uri, nif.beginIndex, Literal(0, datatype=XSD.nonNegativeInteger))
        add_unique_triple(g,context_uri, nif.endIndex, Literal(len(description), datatype=XSD.nonNegativeInteger))
        add_unique_triple(g,context_uri, nif.isString, Literal(description, lang=lang))
        add_unique_triple(g,context_uri, nif.predLang, URIRef(lexvo[lang]))
        #add_unique_triple(g,context_uri, nif.referenceContext, sub)
        add_unique_triple(g,context_uri, nif.wasConvertedFrom, SDO.description)    
        add_unique_triple(g,sub, curriculum_ns.hasAnnotationTarget, context_uri)
        add_unique_triple(g,context_uri, curriculum_ns.isAnnotationTargetOf, sub)

    if keyword:
        context_uri = URIRef(f'{subject}_nif=context_p={keyword_key}_char=0,{len(keyword)}')
        add_unique_triple(g,context_uri, RDF.type, nif.Context)
        #add_unique_triple(g,context_uri, RDF.type, nif.OffsetBasedString)
        add_unique_triple(g,context_uri, nif.beginIndex, Literal(0, datatype=XSD.nonNegativeInteger))
        add_unique_triple(g,context_uri, nif.endIndex, Literal(len(keyword), datatype=XSD.nonNegativeInteger))
        add_unique_triple(g,context_uri, nif.isString, Literal(keyword, lang=lang))
        add_unique_triple(g,context_uri, nif.predLang, URIRef(lexvo[lang]))
        #add_unique_triple(g,context_uri, nif.referenceContext, sub)
        add_unique_triple(g,context_uri, nif.wasConvertedFrom, SDO.keywords)    
        add_unique_triple(g,sub, curriculum_ns.hasAnnotationTarget, context_uri)
        add_unique_triple(g,context_uri, curriculum_ns.isAnnotationTargetOf, sub)

    return g

def add_dbpedia_annotations_wlo(g, subject, name, description, keyword, keyword_key, lang):                    
    context_uri_list = [
        {'p': 'name', 'text_to_annotate': name},
        {'p': 'description', 'text_to_annotate': description},
        {'p': f'{keyword_key}', 'text_to_annotate': keyword}                
    ]

    for item in context_uri_list:

        text_to_annotate = item['text_to_annotate']
        if text_to_annotate:
            context_uri = URIRef(f'{subject}_nif=context_p={item["p"]}_char=0,{len(text_to_annotate)}')

            headers = {
                "Accept": "application/json",
            }
            
            params = {
                "text": text_to_annotate,
            }
            try:
                response = requests.get(spotlight_url[lang], params=params, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()        
                    annotations = data.get("Resources", [])

                    for _, annotation in enumerate(annotations, start=1):            
                        surface_form = annotation.get("@surfaceForm", "")
                        start_index = int(annotation.get("@offset", 0))
                        end_index = start_index + len(surface_form)
                        annotation_uri = URIRef(f'{subject}_a=dbpedia-spotlite_p={item["p"]}_char={start_index},{end_index}')
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
                else:
                    print(f"Error: {response.status_code} - {response.text}")
            except:
                pass

    return g    

def add_wordnet_annotations_wlo(g, subject, name, description, keyword, keyword_key, lang):            
    context_uri_list = [
        {'p': 'name', 'text_to_annotate': name},
        {'p': 'description', 'text_to_annotate': description},
        {'p': f'{keyword_key}', 'text_to_annotate': keyword}                
    ]
    exclusions = ['--',"'", "...", "…", "`", '"', '|', '-', '.', ':', '!', '?', ',', '%', '^', '(', ')', '$', '#', '@', '&', '*']
    
    for item in context_uri_list:
        if item["text_to_annotate"]:
            context_uri = URIRef(f'{subject}_nif=context_p={item["p"]}_char=0,{len(item["text_to_annotate"])}')

            tag_results = tag_text(item["text_to_annotate"], lang)
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
                                
                if len([x for x in exclusions if x in t[0]]) <= 0 and t[1] in ['VERB', 'NOUN', 'ADV', 'ADJ']:                
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
                    
                    if len(words) > 100:
                        print(f"{value.lemma} - {value.pos} > 100 results")

                    for word in words[:30]:
                        weighted_word = WeightedWord(word)  
                        start_idx = 0 if index - CONTEXT_MARGIN < 0 else index - CONTEXT_MARGIN
                        end_idx = len(merge_results) if index + CONTEXT_MARGIN >= len(merge_results) else index + CONTEXT_MARGIN
                        sub_text = ' '.join([x.name for x in merge_results[start_idx:end_idx]])
                        words_to_compare = word_compare_lookup[f'{lang}_1'][f'{lang}-1-{word.ili}']                                         
                        weighted_word.weight = classifier.classify(sub_text, words_to_compare)                                                              
                        weighted_words.append(weighted_word)
                        
                    if len(weighted_words) > 0:                        
                        selected_word = max(weighted_words, key=lambda obj: obj.weight).word    
                        start_index = len(''.join([obj.name + obj.whitespace for obj in merge_results[:index]]))
                        end_index = start_index + len(value.name)
                        annotation_uri = URIRef(f'{subject}_a=spacy_p={item["p"]}_char={start_index},{end_index}')
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


def wlo_part_async(graph, results, thread_nr, lang=None):
    start_time = dt.now()
    cntr = 0        
    for result in results:
        subject = result["s"]["value"]                 
        name = remove_html_tags_and_whitespace(result["name"]["value"]) if 'name' in result else None               
        description = remove_html_tags_and_whitespace(result["description"]["value"]) if 'description' in result else None                                                
                        
        try:
            if description:
                lang = detect(description)                
            elif name:    
                lang = detect(name)                
        except:
            lang = 'en'
                            
        if (name or description) and lang == 'de':                
            add_nif_context_wlo(graph, subject, name, description, None, '_', lang)
            add_dbpedia_annotations_wlo(graph, subject, name, description, None, '_', lang)
            add_wordnet_annotations_wlo(graph, subject, name, description, None, '_', lang)
        cntr +=1
        if (cntr % 10 == 0):                                                
            print(f'{cntr} results of {len(results)} in thread {thread_nr} processed')
            end_time = dt.now()
            elapsed = end_time - start_time
            print(f'Running time for thread {thread_nr} (wlo): {elapsed.seconds // 3600}:{elapsed.seconds // 60 % 60}')
    
    return graph        

def get_keyword_key(subject):
    keyword_key_cntr[subject] += 1
    return f'keyword{keyword_key_cntr[subject]}'

def wlo_part_keywords_async(graph, results, thread_nr, lang=None):
    start_time = dt.now()
    cntr = 0        
    for result in results:
        subject = result["s"]["value"]                         
        keyword = remove_html_tags_and_whitespace(result["keywords"]["value"]) if 'keywords' in result else None                                        
                        
        # try:
        #     if keyword:
        #         lang = detect(keyword)                
        # except:
        #     lang = 'en'
        lang = 'de'
                            
        if (keyword) and lang == 'de':                
            key = get_keyword_key(subject)
            add_nif_context_wlo(graph, subject, None, None, keyword, key, lang)
            add_dbpedia_annotations_wlo(graph, subject, None, None, keyword, key, lang)
            add_wordnet_annotations_wlo(graph, subject, None, None, keyword, key, lang)
        cntr +=1
        if (cntr % 10 == 0):                                                
            print(f'{cntr} results of {len(results)} in thread {thread_nr} processed')
            end_time = dt.now()
            elapsed = end_time - start_time
            print(f'Running time for thread {thread_nr} (kewords): {elapsed.seconds // 3600}:{elapsed.seconds // 60 % 60}')
    
    return graph            

def get_nif_literals_wlo_keywords_async(thread_cnt, thread_nr):
    sparql = SPARQLWrapper("https://edu.yovisto.com/sparql")
    list_length = 1140255
    part_length = list_length // thread_cnt    
    query = """
    select distinct * where {                                                                   
                OPTIONAL { 
                    ?s <https://schema.org/keywords> ?keywords . 
                }                 
             }                            
    """ 
    query += f'LIMIT {part_length} OFFSET {part_length * thread_nr}'

    graph = Graph()            
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()["results"]["bindings"]    
    graph = wlo_part_keywords_async(graph, results, thread_nr)                

    return graph

def get_nif_literals_wlo_async(thread_cnt, thread_nr):
    nlp['de'].max_length = 3000000
                         
    sparql = SPARQLWrapper("https://edu.yovisto.com/sparql")
    list_length = 164843
    part_length = list_length // thread_cnt    
    query = """
    select distinct * where {                                  
                ?s a <https://edu.yovisto.com/ontology/wlo/Resource>  .
                OPTIONAL { 
                    ?s <https://schema.org/name>  ?name . 
                }         
                OPTIONAL { 
                    ?s <https://schema.org/description> ?description . 
                }                                                  
             }                            
    """ 
    query += f'LIMIT {part_length} OFFSET {part_length * thread_nr}'

    graph = Graph()            
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()["results"]["bindings"]        
    graph = wlo_part_async(graph, results, thread_nr)                

    return graph

def get_nif_literals_wlo():
    #nlp.max_length = 3000000
                         
    sparql = SPARQLWrapper("https://edu.yovisto.com/sparql")
    sparql_queries = [    
    """
    select distinct * where {                                  
                ?s a <https://edu.yovisto.com/ontology/wlo/Resource>  .
                OPTIONAL { 
                    ?s <https://schema.org/name>  ?name . 
                }         
                OPTIONAL { 
                    ?s <https://schema.org/description> ?description . 
                }                 
                OPTIONAL { 
                    ?s <https://schema.org/keywords> ?keywords . 
                }                 
             }                           
     
    """
    ]
    
    start_time = dt.now()

    graph = Graph()
    for query in sparql_queries:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()    
        
        cntr = 0
        for result in results["results"]["bindings"]:
            subject = result["s"]["value"]                
            name = result["name"]["value"]                
            description = result["description"]["value"]                                        
            keywords = result["keywords"]["value"]                                        
            name = remove_html_tags_and_whitespace(name)
            description = remove_html_tags_and_whitespace(description)            
            keywords = remove_html_tags_and_whitespace(keywords)            
            lang = 'en'
            if description:
                lang = detect(description)                
            elif name:    
                lang = detect(name)
            elif keywords:
                lang = detect(keywords)
                    
            if lang not in ['en', 'de']:
                    lang = 'en'        
            if (name or description or keywords) and lang == 'de':                
                add_nif_context_wlo(graph, subject, name, description, keywords, lang)
                add_dbpedia_annotations_wlo(graph, subject, name, description, keywords, lang)
                add_wordnet_annotations_wlo(graph, subject, name, description, keywords, lang)
            cntr +=1
            if (cntr % 100 == 0):                                                
                print(f'{cntr} results of {len(results["results"]["bindings"])} processed')
                end_time = dt.now()
                elapsed = end_time - start_time
                print(f'Running time: {elapsed.seconds // 3600}:{elapsed.seconds // 60 % 60}')

    return graph       
                               

#Main Program
CONTEXT_MARGIN = 15

if len(sys.argv) == 4:
    thread_cnt = int(sys.argv[1])
    thread_nr = int(sys.argv[2])
    category = sys.argv[3]

    if category == 'wlo':
        graph = get_nif_literals_wlo_async(thread_cnt, thread_nr)            
        output_file = f"wlo_nif_{thread_nr}.ttl"    
        graph.serialize(destination=output_file, format="turtle", encoding='UTF-8')            
    
    if category == 'keywords':
        keyword_key_cntr = defaultdict(int)
        graph = get_nif_literals_wlo_keywords_async(thread_cnt, thread_nr)            
        output_file = f"wlo_nif_keywords_{thread_nr}.ttl"    
        graph.serialize(destination=output_file, format="turtle", encoding='UTF-8')            
        
else:
    graph = get_nif_literals_wlo()            
    output_file = "wlo_nif.ttl"    
    graph.serialize(destination=output_file, format="turtle", encoding='UTF-8')          



