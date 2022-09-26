# prod
curl --data-urlencode "query=SELECT ?g (COUNT(*) as ?triples) WHERE { GRAPH ?g { ?s ?p ?o } } GROUP BY ?g" http://data-iremus.huma-num.fr/sparql

# local
curl --data-urlencode "query=SELECT ?g (COUNT(*) as ?triples) WHERE { GRAPH ?g { ?s ?p ?o } } GROUP BY ?g" http://localhost:3030/iremus/sparql