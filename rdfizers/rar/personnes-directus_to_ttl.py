from rdflib import Graph, Namespace, DCTERMS, RDF, SKOS, URIRef, URIRef as u, Literal as l
import argparse
from sherlockcachemanagement import Cache
import requests
import os
import sys
import yaml
import json

sys.path.append(os.path.abspath(os.path.join('directus/', '')))  # nopep8
from helpers_graphql_api import graphql_query  # nopep8

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--ttl")
parser.add_argument("--cache")
parser.add_argument("--directus_secret")
args = parser.parse_args()

# Directus secret
file = open(args.directus_secret)
secret = yaml.full_load(file)

# Cache
print(f"Lecture du cache [{args.cache}]")
cache = Cache(args.cache)

############################################################################################
# INITIALISATION DU GRAPHE ET NAMESPACES
############################################################################################

g = Graph()

crm_ns = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
iremus_ns = Namespace("http://data-iremus.huma-num.fr/id/")
sdt_ns = Namespace("http://data-iremus.huma-num.fr/datatypes/")
sherlock_ns = Namespace("http://data-iremus.huma-num.fr/ns/sherlock#")

g.bind("crm", crm_ns)
g.bind("dcterms", DCTERMS)
g.bind("skos", SKOS)
g.bind("sdt", sdt_ns)
g.bind("she_ns", sherlock_ns)

############################################################################################
# DIRECTUS
############################################################################################

print("Récupération des données Directus...")

query = """
query {
    personnes(limit: -1) {
        id
        label
        definition
        note_historique
        ref_iremus
        ref_hortus
        alt_label_1
        alt_label_2
        alt_label_3
        alt_label_4
        alt_label_5
        alt_label_6
        alt_label_7
        alt_label_8
        alt_label_9
        alt_label_10
        alt_label_11
        data_bnf_alignement
        catalogue_bnf_alignement
        viaf_alignement
        isni_alignement
        versailles_alignement
    }
}"""

result = graphql_query(query, secret)

############################################################################################
# RDF
############################################################################################

print("Génération du graphe RDF...")

# Référentiel des personnes
E32_personnes_uri = u(iremus_ns["947a38f0-34ac-4c54-aeb7-69c5f29e77c0"])

for personne in result["data"]["personnes"]:
    E21_uuid = personne["id"]
    E21_uri = iremus_ns[E21_uuid]
    g.add((E21_uri, RDF.type, crm_ns["E21_Person"]))
    g.add((E32_personnes_uri, crm_ns["P71_lists"], E21_uri))

    # PrefLabel
    E41_uri = iremus_ns[cache.get_uuid(
        ["personnes", E21_uuid, "E41_pref"], True)]
    g.add((E21_uri, crm_ns["P1_is_identified_by"], E41_uri))
    g.add((E41_uri, RDF.type, crm_ns["E41_Appellation"]))
    g.add((E41_uri, crm_ns["P190_has_symbolic_content"], l(personne["label"])))
    # Preferred Appellation
    g.add((E41_uri, crm_ns["P2_has_type"],
           iremus_ns["3cf0c743-ee9b-4dfc-8133-7dd383a1b6be"]))

    # AltLabels
    for label_index in range(1, 12):
        clef = "alt_label_" + str(label_index)
        altlabel = personne[clef]
        if altlabel:
            E41_alt_uri = iremus_ns[cache.get_uuid(["personnes", E21_uuid, "E41_alt", altlabel], True)]
            g.add((E41_alt_uri, RDF.type, crm_ns["E41_Appellation"]))
            g.add((E41_alt_uri, iremus_ns["P190_has_symbolic_content"], l(altlabel)))
            g.add((E21_uri, crm_ns["P1_is_identified_by"], E41_alt_uri))
            # Alternative Appellation
            g.add((E41_alt_uri, crm_ns["P2_has_type"], iremus_ns["70589b95-4156-431e-a58a-818af6dc795a"]))

    # Définition - Removed usage of E13 since all the authority document is signed, not only notes
    if personne["definition"] != None:
        g.add((E21_uri, sherlock_ns["definition"], l(personne["definition"])))

    # Note historique - Removed usage of E13 since all the authority document is signed, not only notes
    if personne["note_historique"] != None:
        g.add((E21_uri, crm_ns["P3_has_note"], l(personne["note_historique"])))


    # ASSOCIATING E42

    def linkE42(champ, E55_uuid):
        """
        Generate turtle for an identifier in person collection.

        :param str champ: field as it is defined in Directus
        :param str E55_uuid: uuid of the type of alignement
        """

        if personne[champ]:
            E42_alignement = iremus_ns[cache.get_uuid(["personnes", E21_uuid, "E42", champ], True)]
            g.add((E21_uri, crm_ns["P1_is_identified_by"], E42_alignement))
            g.add((E42_alignement, crm_ns['P2_has_type'], iremus_ns[E55_uuid]))
            g.add((E42_alignement, crm_ns['P190_has_symbolic_content'], l(personne[champ])))


    linkE42(champ="versailles_alignement", E55_uuid="f316e967-0a73-442a-a6b9-e1de5171f247")
    linkE42(champ="data_bnf_alignement", E55_uuid="df9f27d6-b08b-46e6-ad67-202259c4cdbd")
    linkE42(champ="catalogue_bnf_alignement", E55_uuid="59835932-52aa-4a19-ac6e-916d2a4b9228")
    linkE42(champ="isni_alignement", E55_uuid="49729025-e609-46ed-a749-5f3ae53dbfbe")

    # Les identifiants IReMus/Hortus seront éventuellement supprimés par Nathalie dans Directus
    linkE42(champ="ref_hortus", E55_uuid="6703d6e9-bd46-4c7d-865e-5e5a4c0a549f")
    linkE42(champ="ref_iremus", E55_uuid="6e2effb0-1dd6-4693-a9bb-f3ceb7dfe6fc")

############################################################################################
# TESTS
############################################################################################
print("Test du graphe généré...")

triples = list(g.triples((None, RDF.type, URIRef(value="E21_Person", base="http://www.cidoc-crm.org/cidoc-crm/"))))
assert len(triples) == len(result["data"]["personnes"]), "Equal number of person in Directus and Turtle"

############################################################################################
# SERIALISATION DU GRAPHE
############################################################################################

print(f"Sérialisation du graphe [{args.ttl}]...")
serialization = g.serialize(format="turtle", base="http://data-iremus.huma-num.fr/id/")
with open(args.ttl, "w+") as f:
    f.write(serialization)

cache.bye()
