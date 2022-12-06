import requests, json, argparse, urllib
from sherlockcachemanagement import Cache
from rdflib import Graph, Namespace, URIRef, RDF, Literal


parser = argparse.ArgumentParser()
parser.add_argument("--ttl")
parser.add_argument("--cache")
args = parser.parse_args()

# Cache
print(f"Lecture du cache [{args.cache}]")
cache = Cache(args.cache)


output_graph = Graph()

crm_ns = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
iremus_ns = Namespace("http://data-iremus.huma-num.fr/id/")
sherlock_ns = Namespace("http://data-iremus.huma-num.fr/ns/sherlock#")

output_graph.bind("crm", crm_ns)
output_graph.bind("she_ns", sherlock_ns)

def crm(x):
    return URIRef(crm_ns[x])

def she(x):
    return URIRef(iremus_ns[x])

def t(s, p, o):
    output_graph.add((s, p, o))

########################################################################################
# GET ORCID IDS BY USERS 
########################################################################################
print("Fetching Sherlock user data...")

query = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
select ?user ?orcid
where {
 	graph ?g {
		?user rdf:type crm:E21_Person.
    	?user crm:P1_is_identified_by ?identifier.
    	?identifier rdf:type crm:E42_Identifier.
    	?identifier crm:P2_has_type <http://data-iremus.huma-num.fr/id/d7ef2583-ff31-4913-9ed3-bc3a1c664b21>.
    	?identifier crm:P190_has_symbolic_content ?orcid	
  	}
}
"""
r = requests.get("http://data-iremus.huma-num.fr/sparql?query=" + urllib.parse.quote((query)))
result = json.loads(r.text)

########################################################################################
# FETCH ORCID USER INFOS (TODO: PARALLELIZE API CALLS)
########################################################################################

print("Fetching Orcid user infos...")

user_dict = {}
for row in result["results"]["bindings"]:
    response = requests.get(f"https://pub.orcid.org/v3.0/{row['orcid']['value']}/", headers = { 'Content-Type' : 'application/json' })
    user = response.json()
    user_dict[row["user"]["value"].split("/")[-1]] = f'{user["person"]["name"]["given-names"]["value"]} {user["person"]["name"]["family-name"]["value"]}'

########################################################################################
# CREATE RDF TRIPLES
########################################################################################
print("Creating RDF triples")
for uuid, name in user_dict.items():
    E41_name = she(cache.get_uuid(["user", uuid, "E41_orcid"], True))
    t(she(uuid), crm("P1_is_identified_by"), E41_name)
    t(E41_name, RDF.type, crm("E41_Appellation"))
    t(E41_name, crm("P2_has_type"), she("73ea8d74-3526-4f6a-8830-dd369795650d"))
    t(E41_name, crm("P190_has_symbolic_content"), Literal(name))

#########################################################################################
# SERIALISATION DU GRAPHE
#########################################################################################

print(f"Sérialisation du graphe [{args.ttl}]...")
serialization = output_graph.serialize(format="turtle", base="http://data-iremus.huma-num.fr/id/")
with open(args.ttl, "w+") as f:
    f.write(serialization)

cache.bye()