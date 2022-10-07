# SEMANTIC DEPENDENCIES TO data/mercure-galant.ttl

from rdflib import Graph, Namespace, DCTERMS, RDF, RDFS, SKOS, URIRef, URIRef as u, Literal as l
import argparse
from sherlockcachemanagement import Cache
import requests
import os
import sys
import yaml
import json

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--ttl")
parser.add_argument("--cache")
args = parser.parse_args()

# Cache
print(f"Lecture du cache [{args.cache}]")
cache = Cache(args.cache)

# Secret YAML
file = open(os.path.join(sys.path[0], "secret.yaml"))
secret = yaml.full_load(file)
query =f"""mutation {{
    auth_login(email: "{secret["email"]}", password: "{secret["password"]}") {{
        access_token
        refresh_token
    }}
}}"""
r = requests.post(secret["url"] + 'system', json={'query': query})

access_token = r.json()['data']['auth_login']['access_token']
file.close()

############################################################################################
# INITIALISATION DU GRAPHE ET NAMESPACES
############################################################################################

output_graph = Graph()

crm_ns = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
iremus_ns = Namespace("http://data-iremus.huma-num.fr/id/")
sdt_ns = Namespace("http://data-iremus.huma-num.fr/datatypes/")
sherlock_ns = Namespace("http://data-iremus.huma-num.fr/ns/sherlock#")

output_graph.bind("crm", crm_ns)
output_graph.bind("dcterms", DCTERMS)
output_graph.bind("skos", SKOS)
output_graph.bind("sdt", sdt_ns)
output_graph.bind("she_ns", sherlock_ns)

a = RDF.type


def crm(x):
    return URIRef(crm_ns[x])


def she(x):
    return URIRef(iremus_ns[x])


def she_ns(x):
    return URIRef(sherlock_ns[x])


def t(s, p, o):
    output_graph.add((s, p, o))


############################################################################################
# RECUPERATION DES DONNEES DANS DIRECTUS
############################################################################################

print("Récupération des données Directus…")

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
    viaf_alignement
    catalogue_bnf_alignement
    versailles_alignement
    data_bnf_alignement
    isni_alignement
	} 
}"""

r = requests.post(secret["url"] + '?access_token=' + access_token, json={'query': query})
result = json.loads(r.text)

############################################################################################
# CREATION DES TRIPLETS
############################################################################################

print("Création des triplets RDF…")

E32_personnes_uri = u(iremus_ns["947a38f0-34ac-4c54-aeb7-69c5f29e77c0"]) #Référentiel des personnes
t(E32_personnes_uri, a, crm("E32_Authority_Document"))
t(E32_personnes_uri, crm("P1_is_identified_by"), l("Noms de personnes"))

for personne in result["data"]["personnes"]:
    E21_uuid = personne["id"]
    E21_uri = she(E21_uuid)
    t(E21_uri, a, crm("E21_Person"))
    t(E32_personnes_uri, crm("P71_lists"), E21_uri)

    # PrefLabel
    E41_uri = she(cache.get_uuid(["personnes", E21_uri, "E41"], True))
    t(E21_uri, crm("P1_is_identified_by"), E41_uri)
    t(E41_uri, a, crm("E41_Appellation"))
    t(E41_uri, RDFS.label, l(personne["label"]))
    t(E41_uri, crm("P2_has_type"), she("3cf0c743-ee9b-4dfc-8133-7dd383a1b6be")) #Preferred Appellation

    # AltLabels
    n = 1
    clé = "alt_label_" + str(n)
    while clé in personne.keys():
        altlabel = personne[clé]
        if altlabel != None:
            E41_alt_uri = she(cache.get_uuid(["personnes", E21_uri, "E41 alt", altlabel], True))
            t(E41_alt_uri, a, crm("E41_Appellation"))
            t(E41_alt_uri, RDFS.label, l(altlabel))
            t(E21_uri, crm("P1_is_identified_by"), E41_alt_uri)
            t(E41_alt_uri, crm("P2_has_type"), she("70589b95-4156-431e-a58a-818af6dc795a")) #Alternative Appellation
        n += 1
        clé = "alt_label_" + str(n)

    # Définition
    if personne["definition"] != None:
        E13_definition_uri = she(cache.get_uuid(["personnes", E21_uri, "definition", "E13"], True))
        t(E13_definition_uri, a, crm("E13_Attribute_Assignement"))
        t(E13_definition_uri, crm("P14_carried_out_by"), she("684b4c1a-be76-474c-810e-0f5984b47921")) #Equipe Mercure Galant
        t(E13_definition_uri, crm("P140_assigned_attribute_to"), E21_uri)
        t(E13_definition_uri, crm("P141_assigned"), l(personne["definition"]))
        t(E13_definition_uri, crm("P177_assigned_property_type"), she_ns("definition"))

    # Note historique
    if personne["note_historique"] != None:
        E13_note_uri = she(cache.get_uuid(["personnes", E21_uri, "note historique", "E13"], True))
        t(E13_note_uri, a, crm("E13_Attribute_Assignement"))
        t(E13_note_uri, crm("P14_carried_out_by"), she("684b4c1a-be76-474c-810e-0f5984b47921")) #Equipe Mercure Galant
        t(E13_note_uri, crm("P140_assigned_attribute_to"), E21_uri)
        t(E13_note_uri, crm("P141_assigned"), l(personne["note_historique"]))
        t(E13_note_uri, crm("P177_assigned_property_type"), crm("P3_has_note"))

    # Les identifiants IReMus/Hortus seront éventuellement supprimés par Nathalie dans Directus

    # # Identifant IReMus
    if personne["ref_iremus"] != None: 
        E42_ref_iremus = she(cache.get_uuid(["personnes", E21_uri, "E42 ref iremus"], True))
        t(E21_uri, crm("P1_is_identified_by"), E42_ref_iremus)
        t(E42_ref_iremus, crm('P2_has_type'), she("6e2effb0-1dd6-4693-a9bb-f3ceb7dfe6fc") ) #Identifiant IReMus
        t(E42_ref_iremus, crm('P190_has_symbolic_content'), l(personne["ref_iremus"]))

    # Identifiant Hortus
    if personne["ref_hortus"] != None:
        E42_ref_hortus = she(cache.get_uuid(["personnes", E21_uri, "E42 ref hortus"], True))
        t(E21_uri, crm("P1_is_identified_by"), E42_ref_hortus)
        t(E42_ref_iremus, crm('P2_has_type'), she("6703d6e9-bd46-4c7d-865e-5e5a4c0a549f") ) #Identifiant Hortus
        t(E42_ref_iremus, crm('P190_has_symbolic_content'), l(personne["ref_hortus"]))

    # Alignements
    def alignement(champ, E55_uuid):
        """
        Generate turtle for an alignement in person collection.

        :param str champ: field as it is defined in Directus
        :param str E55_uuid: uuid of the type of alignement
        """

        if personne[champ] != None:
            E42_alignement = she(cache.get_uuid(["personnes", E21_uri, champ], True))
            t(E21_uri, crm("P1_is_identified_by"), E42_alignement)
            t(E42_alignement, crm('P2_has_type'), she(E55_uuid))
            t(E42_alignement, crm('P190_has_symbolic_content'), l(personne[champ]))

    alignement(champ = "versailles_alignement", E55_uuid = "f316e967-0a73-442a-a6b9-e1de5171f247")
    alignement(champ = "data_bnf_alignement", E55_uuid = "df9f27d6-b08b-46e6-ad67-202259c4cdbd")
    alignement(champ = "catalogue_bnf_alignement", E55_uuid= "59835932-52aa-4a19-ac6e-916d2a4b9228")
    alignement(champ = "isni_alignement", E55_uuid = "49729025-e609-46ed-a749-5f3ae53dbfbe")

############################################################################################
# TESTS
############################################################################################
print("Test du graphe généré...")

triples = list(output_graph.triples((None, RDF.type, URIRef(value = "E21_Person", base= "http://www.cidoc-crm.org/cidoc-crm/"))))
assert len(triples) == len(result["data"]["personnes"]), "Equal number of person in Directus and Turtle"

############################################################################################
# SERIALISATION DU GRAPHE
############################################################################################

print(f"Sérialisation du graphe [{args.ttl}]...")
serialization = output_graph.serialize(format="turtle", base="http://data-iremus.huma-num.fr/id/")
with open(args.ttl, "w+") as f:
    f.write(serialization)

cache.bye()
