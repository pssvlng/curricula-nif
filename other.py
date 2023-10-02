
from rdflib import Graph
graph = Graph()
for i in range (0, 10):
    print(i)
    g = Graph()
    g.parse(f'oersi_nif_{i}.ttl', format='ttl')
    graph += g

output_file = "oersi_nif.ttl"    
graph.serialize(destination=output_file, format="turtle", encoding='UTF-8')            