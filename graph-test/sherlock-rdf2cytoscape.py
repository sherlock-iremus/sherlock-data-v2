# https://cytoscape.org/javadoc/3.7.2/org/cytoscape/view/presentation/property/BasicVisualLexicon.html

import argparse
from functools import reduce
import pandas as pd
from pprint import pprint
import py4cytoscape as p4c
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS, SKOS
import requests

################################################################################
# CONSTANTS
################################################################################

BASE = Namespace("http://data-iremus.huma-num.fr/id/")
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
CRMDIG = Namespace("http://www.ics.forth.gr/isl/CRMdig/")
GUILLOTEL_2022 = Namespace("http://modality-tonality.huma-num.fr/Guillotel_2022#")
SHERLOCK_NS = Namespace("http://data-iremus.huma-num.fr/ns/sherlock#")
ZARLINO1588 = Namespace("http://modality-tonality.huma-num.fr/Zarlino_1558#")
EXCLUDED_PREDICATES_PREFIXES = [
    str(DCTERMS),
    str(RDF),
    str(RDFS),
    str(SHERLOCK_NS["has_document_context"]),
    str(CRM["P1_is_identified_by"]),
    str(CRM["P2_has_type"])
]
PREFIXES = {
    BASE: "",
    CRM: "crm",
    CRMDIG: "crmdig",
    DCTERMS: "dcterms",
    GUILLOTEL_2022: "cgn",
    RDF: "rdf",
    RDFS: "rdfs",
    SKOS: "skos",
    SHERLOCK_NS: "sherlock",
    ZARLINO1588: "zar",
}
TYPE_COLORS = {
    CRM["E13_Attribute_Assignment"]: {"bg": "purple", "label": "white"},
}
ALL_NAMESPACES = PREFIXES.keys()
AUTONOMOUS_PREDICATES_AS_P177 = [CRM["P2_has_type"], CRM["P67_refers_to"], URIRef("http://modality-tonality.huma-num.fr/Guillotel_2022#hasLine")]

################################################################################
# SETUP
################################################################################

parser = argparse.ArgumentParser()
parser.add_argument("--rdf")
args = parser.parse_args()

g = Graph()
g.parse(args.rdf)

r = requests.post("http://localhost:1234/v1/commands/network/create empty", json={"name": args.rdf})
network_id = r.json()["data"]["network"]
r = requests.get("http://localhost:1234/v1/networks/views/currentNetworkView")
network_view_id = r.json()["data"]["networkViewSUID"]

################################################################################
# STATE
################################################################################

resources = []
created_nodes = {}
autonomous_predicates_as_p177_counters = {}
for p in AUTONOMOUS_PREDICATES_AS_P177:
    autonomous_predicates_as_p177_counters[str(p)] = 0


################################################################################
# HELPERS
################################################################################


def strip_namespace(iri):
    for ns in ALL_NAMESPACES:
        if iri in ns:
            return str(PREFIXES[ns]) + ":" + str(iri).replace(str(ns), '')
    return iri


def get_p1(iri):
    triples = list(g.triples((iri, CRM["P1_is_identified_by"], None)))
    if len(triples) > 0:
        return str(triples[0][2])
    else:
        return ""


def get_crm_code(iri):
    if str(CRMDIG) in iri:
        return iri.replace(CRMDIG, '').split("_")[0]
    return iri.replace(CRM, '').split("_")[0]


def get_rdf_types(iri):
    return [triple[2] for triple in g.triples((URIRef(iri), RDF.type, None))]


def make_label(iri):
    if iri not in resources:
        resources.append(iri)

    # Lister les types de la ressource courante

    rdf_types = get_rdf_types(iri)
    rdf_types_labels = [get_crm_code(rdf_type) for rdf_type in rdf_types]
    crm_p2_types = [triple[2] for triple in g.triples((URIRef(iri), CRM["P2_has_type"], None))]
    crm_p2_types_labels = [get_p1(i) for i in crm_p2_types]

    label_parts = ["[" + str(resources.index(iri) + 1) + "]" + (" " if len(rdf_types_labels) else "") + " ".join(rdf_types_labels)]
    if (len(crm_p2_types)):
        label_parts.append(" ".join(crm_p2_types_labels))
    p1 = get_p1(URIRef(iri))
    if p1:
        label_parts.append(p1)
    if len(rdf_types) == 0 and len(crm_p2_types) == 0:
        iri_name = strip_namespace(iri)
        if "___" in iri_name:
            iri_name = iri_name.split("___")[0]
        label_parts.append(iri_name)
    label_parts = [p if len(p) < 50 else p[:50] for p in label_parts]

    return {
        "label": "\n".join(label_parts),
        "width": len(max(label_parts, key=len)),
        "height": len(label_parts)
    }


def style_node(iri, suid):
    rdf_types = get_rdf_types(URIRef(iri))
    node_color = "darkturquoise"
    node_label_color = "black"
    for rdf_type in TYPE_COLORS:
        if rdf_type in rdf_types:
            node_color = TYPE_COLORS[rdf_type]["bg"]
            node_label_color = TYPE_COLORS[rdf_type]["label"]

    label_data = make_label(iri)
    label = label_data["label"]
    label_width = label_data["width"] * 7
    label_height = label_data["height"] * 15

    url = f"http://localhost:1234/v1/networks/{network_id}/views/{network_view_id}/nodes/{suid}?bypass=true"
    r = requests.put(url, json=[
        {"visualProperty": "NODE_LABEL_FONT_FACE", "value": "AmericanTypewriter-Condensed"},
        {"visualProperty": "NODE_LABEL_WIDTH", "value": label_width},
        {"visualProperty": "NODE_WIDTH", "value": label_width},
        {"visualProperty": "NODE_HEIGHT", "value": label_height},
        {"visualProperty": "NODE_LABEL", "value": label},
        {"visualProperty": "NODE_PAINT", "value": node_color},
        {"visualProperty": "NODE_LABEL_COLOR", "value": node_label_color},
        {"visualProperty": "NODE_SELECTED_PAINT", "value": "aquamarine"},
    ])


def style_edge(iri, suid):
    url = f"http://localhost:1234/v1/networks/{network_id}/views/{network_view_id}/edges/{suid}?bypass=true"
    r = requests.put(url, json=[
        {"visualProperty": "EDGE_LABEL_FONT_FACE", "value": "AmericanTypewriter-Condensed"},
        {"visualProperty": "EDGE_TARGET_ARROW_SHAPE", "value": "opendelta"},
        {"visualProperty": "EDGE_PAINT", "value": "darkorange"},
        {"visualProperty": "EDGE_SELECTED_PAINT", "value": "gold"},
        {"visualProperty": "EDGE_LABEL_COLOR", "value": "black"},
        {"visualProperty": "EDGE_LABEL", "value": strip_namespace(iri)},
    ])


def ignore_triple(s, p, o):
    for predicate_prefix in EXCLUDED_PREDICATES_PREFIXES:
        if str(p).startswith(predicate_prefix):
            return True

    # On exclut les triplets qui sortent d'une ressource utilisée comme un type
    resources_that_have_s_as_type = reduce(lambda x, y: x+y, map(lambda tp: list(g.triples((None, tp, s))), [RDF.type, CRM["P2_has_type"]]))
    if len(resources_that_have_s_as_type) > 0:
        return True


################################################################################
# PROCESS
################################################################################


for s, p, o in g:
    s = str(s)
    p = str(p)
    o = str(o)

    if ignore_triple(s, p, o):
        continue

    # S

    s_suid = None

    if s not in created_nodes:
        created_node_s = requests.post(f"http://localhost:1234/v1/networks/{network_id}/nodes", json=[s]).json()[0]
        s_suid = created_node_s["SUID"]
        style_node(s, s_suid)
        created_nodes[s] = s_suid
    else:
        s_suid = created_nodes[s]

    # O

    o_suid = None

    if URIRef(o) in AUTONOMOUS_PREDICATES_AS_P177:
        autonomous_predicates_as_p177_counters[o] += 1
        o = o + "___" + str(autonomous_predicates_as_p177_counters[o])

    if o not in created_nodes:
        created_node_o = requests.post(f"http://localhost:1234/v1/networks/{network_id}/nodes", json=[o]).json()[0]
        o_suid = created_node_o["SUID"]
        style_node(o, o_suid)
        created_nodes[o] = o_suid
    else:
        o_suid = created_nodes[o]

    # P

    created_edge = requests.post(f"http://localhost:1234/v1/networks/{network_id}/edges", json=[{
        "source": s_suid,
        "target": o_suid,
        "directed": True
    }]).json()[0]

    style_edge(p, created_edge["SUID"])

print("NETWORK ID:", network_id)
print("NETWORK VIEW ID:", network_view_id)
