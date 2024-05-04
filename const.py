query_verbs_wikidata = """
SELECT ?lemma ?categoryLabel ?gloss ?example WHERE {
  {
    SELECT ?lemma ?categoryLabel ?gloss ?example WHERE {
      ?l rdf:type ontolex:LexicalEntry;
        dct:language ?language;
        wikibase:lemma ?lemma;
        wikibase:lexicalCategory ?category;
        ontolex:sense ?sense.
      ?language wdt:P218 "en".
      ?sense skos:definition ?gloss.
      ?l p:P5831 ?statement.
      ?statement ps:P5831 ?example.
      FILTER(EXISTS { ?l ontolex:sense ?sense. })
      FILTER((LANG(?gloss)) = "en")
      FILTER((STR(?lemma)) = "drink")
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }    
  }
  FILTER(STR(?categoryLabel) = "verb")
}
LIMIT 1000
"""

query_wikidata_count = """
SELECT (Count(?lemma) as ?countVar) WHERE {
   ?l dct:language ?language ;        
      ontolex:sense ?sense ;
        wikibase:lemma ?lemma .
        #wikibase:lexicalCategory ?category ;
        
    ?language wdt:P218 'en' .
  
  ?sense skos:definition ?gloss .
  #?l skos:definition ?gloss .
  # Usage example
  #?l p:P5831 ?statement .
  #?statement ps:P5831 ?example .  
  #FILTER EXISTS {?l ontolex:sense ?sense }
  FILTER(LANG(?gloss) = "en")  
  SERVICE wikibase:label {
   bd:serviceParam wikibase:language "en" .
  }  
}
"""

query_lod_wikidata = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX wnid: <http://wordnet-rdf.princeton.edu/id/> 
prefix wn: <https://globalwordnet.github.io/schemas/wn#> 

select distinct * where {
  ?wnid  wn:ili ?ili .
  BIND ( replace( str(?wnid),'http://wordnet-rdf.princeton.edu/id/oewn-', '') as ?synset )    
  ?item wdt:P8814 ?synset .
  
} LIMIT 10
"""

query_wlo_desc_inconsistancies = """
select  ?s ?desc ?text  where 
{
?desc <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#wasConvertedFrom> <https://schema.org/description>  .
?desc  <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#isString> ?text .
?desc <https://w3id.org/curriculum/isAnnotationTargetOf> ?s
filter not exists {
?anno <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#referenceContext> ?desc .
?anno <http://www.w3.org/2005/11/its/rdf#taAnnotatorsRef> <https://spacy.io>  .
?anno a <http://purl.org/olia/olia.owl#Verb>  . }
filter not exists {
?anno <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#referenceContext> ?desc .
?anno <http://www.w3.org/2005/11/its/rdf#taAnnotatorsRef> <https://spacy.io>  .
?anno a <http://purl.org/olia/olia.owl#Noun>  . }
filter not exists { 
?anno <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#referenceContext> ?desc .
?anno <http://www.w3.org/2005/11/its/rdf#taAnnotatorsRef> <https://spacy.io>  .
?anno a <http://purl.org/olia/olia.owl#Adjective>  .  }
FILTER(STR(?s) = "https://edu.yovisto.com/resource/wlo/b85471aa-07dd-4398-94dc-52d5151dc547")
}
"""