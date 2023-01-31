import argparse
from functools import reduce
from pprint import pprint
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS, SKOS

BASE = Namespace("http://data-iremus.huma-num.fr/id/")
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
SHERLOCK_NS = Namespace("http://data-iremus.huma-num.fr/ns/sherlock#")
excluded_namespaces = [DCTERMS, RDF, RDFS]
all_namespaces = [BASE, CRM, DCTERMS, RDF, RDFS, SHERLOCK_NS, SKOS]
typing_predicate = [RDF.type, CRM["P2_has_type"]]

parser = argparse.ArgumentParser()
parser.add_argument("--rdf")
args = parser.parse_args()

g = Graph()
g.parse(args.rdf)

ANONYMOUS = "X"
resources = []
iri2label = {}


def strip_namespace(r):
    for n in all_namespaces:
        if r in n:
            return str(r).replace(str(n), '')
    return r


def process_resource(iri):
    # Lister les types de la ressource courante

    rdf_types = [strip_namespace(triple[2]) for triple in list(g.triples((iri, RDF.type, None)))]
    crm_p2_types = [strip_namespace(triple[2]) for triple in list(g.triples((iri, CRM["P2_has_type"], None)))]

    current_resource_types = None
    if len(rdf_types) == 0 and len(crm_p2_types) == 0:
        current_resource_types = [ANONYMOUS]
    else:
        current_resource_types = rdf_types + crm_p2_types

    # Construire le label de la ressource courante

    if iri not in resources:
        resources.append(iri)

    # Construction du label

    p1_values = [triple[2] for triple in list(g.triples((iri, CRM["P1_is_identified_by"], None)))]

    label = " ".join([
        str(resources.index(iri)),
        " ".join(current_resource_types),
        " ".join(p1_values)
    ])

    return label


print("strict digraph {")
print("  layout=sfdp")
print("  nodesep=50")
print("  overlap=false")
print("  node [shape=box]")

for s, p, o in g:

    # On exclut les triplets dont le prédicat appartient à un namespace qui ne nous intéresse pas
    if True in [p in n for n in excluded_namespaces]:
        continue

    # On exclut les triplets dont le prédicat est un prédicat de typage
    if p in typing_predicate:
        continue

    # On exclut les triplets qui sortent d'une ressource utilisée comme un type
    resources_that_have_s_as_type = reduce(lambda x, y: x+y, map(lambda tp: list(g.triples((None, tp, s))), typing_predicate))
    if len(resources_that_have_s_as_type) > 0:
        continue

    s_label = process_resource(s)
    o_label = process_resource(o)
    print(f"  \"{s_label}\" -> \"{o_label}\" [label=\"{strip_namespace(p)}\"]")

print("}")
