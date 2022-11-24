import argparse
import os
from pprint import pprint
import rdflib
import requests
import sys
import yaml
from sherlockcachemanagement import Cache

BASE = "http://bases-iremus.huma-num.fr/directus-catalogue"

parser = argparse.ArgumentParser()
parser.add_argument("--cache")
parser.add_argument("--directus_secret")
parser.add_argument("--owl")
parser.add_argument("--out_ttl")
args = parser.parse_args()

cache = Cache(args.cache)

print("Récupération des données sur les utilisateurs SHERLOCK à partir du SPARQL endpoint")
sherlock_users_orcid_to_uuid = {}
sherlock_users_graph = rdflib.Graph()
res = sherlock_users_graph.query(
    """
    PREFIX sherlock: <http://data-iremus.huma-num.fr/id/>
    PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT ?u ?orcid
    WHERE {
        SERVICE <https://data-iremus.huma-num.fr/sparql> {
            GRAPH ?g {
                ?u rdf:type crm:E21_Person .
                ?u crm:P1_is_identified_by ?e42 .
                ?e42 rdf:type crm:E42_Identifier .
                ?e42 crm:P2_has_type sherlock:d7ef2583-ff31-4913-9ed3-bc3a1c664b21 .
                ?e42 crm:P190_has_symbolic_content ?orcid .
            }
        }
    }
    """
)
for row in res:
    sherlock_users_orcid_to_uuid[str(row.orcid)] = str(row.u)

print("Obtention d'un token d'authentification Directus…")
file = open(args.directus_secret)
secret = yaml.full_load(file)
file.close()
r = requests.post("http://bases-iremus.huma-num.fr/directus-catalogue" + "/auth/login", json={"email": secret["email"], "password": secret["password"]})
access_token = r.json()["data"]["access_token"]
refresh_token = r.json()["data"]["refresh_token"]

print("Chargement des données de Christophe dans un graph interne…")
g = rdflib.ConjunctiveGraph()
g.parse(args.owl, format='xml')

print("Création des annotations…")
def query_get_user_uuid_from_orcid(orcid): return """
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT *
WHERE {
    GRAPH ?g {
        ?e42 rdf:type crm:E42_Identifier .
    }
}
"""


def get_o(x): return str(list(x)[0])


g_out = rdflib.Graph()
crm_ns = rdflib.Namespace("http://www.cidoc-crm.org/cidoc-crm/")
crmdig_ns = rdflib.Namespace("http://www.ics.forth.gr/isl/CRMdig/")
sherlock_ns = rdflib.Namespace("http://data-iremus.huma-num.fr/id/")
sherlockns_ns = rdflib.Namespace("http://data-iremus.huma-num.fr/ns/sherlock#")
g_out.bind("crm", crm_ns)
g_out.bind("dcterms", rdflib.DCTERMS)
g_out.bind("sherlock", sherlockns_ns)

scores_uuid = {}

for a in g.subjects(rdflib.RDF.type, rdflib.URIRef("http://www.tonalities#rootAnnotation")):
    # http://www.tonalities#hasFileName
    fileName = get_o(g.objects(a, rdflib.URIRef("http://www.tonalities#hasFileName")))
    choral_number = fileName.split(".")[0]
    mei_gh_url = f"https://raw.githubusercontent.com/polifonia-project/tonalities_pilot/main/scores/Bach_Chorals/{choral_number}.mei"
    if mei_gh_url in scores_uuid:
        score_uuid = scores_uuid[mei_gh_url]
    else:
        x = requests.get(f"{BASE}/items/partitions?access_token={access_token}&filter[pre_sherlock_url][_eq]={mei_gh_url}")
        x = x.json()["data"]
        score_uuid = x[0]["id"]
        scores_uuid[mei_gh_url] = score_uuid
    score_iri = f"http://data-iremus.huma-num.fr/id/{score_uuid}"

    # http://www.tonalities#hasAnalystName
    # http://www.tonalities#hasORCID
    analyst_orcid = get_o(g.objects(a, rdflib.URIRef("http://www.tonalities#hasORCID")))
    analyst_iri = sherlock_users_orcid_to_uuid[analyst_orcid]

    # http://www.tonalities#hasDateTime
    date = get_o(g.objects(a, rdflib.URIRef("http://www.tonalities#hasDateTime")))

    # http://www.tonalities#hasAbsoluteOffset
    # http://www.tonalities#hasMeasureBeat
    # http://www.tonalities#hasMeasureNumber
    # http://www.tonalities#hasRelativeOffset
    # absolute_offset = get_o(g.objects(a, rdflib.URIRef("http://www.tonalities#hasAbsoluteOffset")))
    measure_beat = get_o(g.objects(a, rdflib.URIRef("http://www.tonalities#hasMeasureBeat")))
    # measure_number = get_o(g.objects(a, rdflib.URIRef("http://www.tonalities#hasMeasureNumber")))
    # relative_offset = get_o(g.objects(a, rdflib.URIRef("http://www.tonalities#hasRelativeOffset")))
    p140 = rdflib.URIRef(f"{score_iri}-{measure_beat}")

    # http://www.tonalities#hasPitch
    p141 = rdflib.Literal(get_o(g.objects(a, rdflib.URIRef("http://www.tonalities#hasPitch"))))

    p177 = rdflib.URIRef("http://data-iremus.huma-num.fr/id/003559fc-f033-4fc3-9c05-0d5f283123ed")

    e13 = sherlock_ns[cache.get_uuid([str(a)], True)]
    g_out.add((e13, rdflib.RDF.type, crm_ns["E13_Attribute_Assignment"]))
    g_out.add((e13, crm_ns["P140_assigned_attribute_to"], p140))
    g_out.add((e13, crm_ns["P177_assigned_property_of_type"], p177))
    g_out.add((e13, crm_ns["P141_assigned"], p141))
    g_out.add((e13, sherlockns_ns["has_document_context"], rdflib.URIRef(score_iri)))
    g_out.add((e13, rdflib.DCTERMS["created"], rdflib.Literal(date, datatype=rdflib.XSD.dateTime)))
    g_out.add((e13, crm_ns["P14_carried_out_by"], rdflib.URIRef(analyst_iri)))

print("Sérialisation finale…")
cache.bye()
g_out.serialize(format='turtle', destination=args.out_ttl, base=sherlock_ns)
