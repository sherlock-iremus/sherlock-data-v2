from rdflib import Graph, Literal, Namespace, DCTERMS, RDF, RDFS, SKOS, URIRef, URIRef as u, Literal as l
import argparse
from pprint import pprint
from sherlockcachemanagement import Cache
import requests
import os
import sys
import yaml
import json
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport


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
r = requests.post(secret["url"] + "/auth/login", json={"email": secret["email"], "password": secret["password"]})
access_token = r.json()['data']['access_token']
refresh_token = r.json()['data']['refresh_token']
file.close()

# Sélection de l'URL des requêtes GraphQL et création d'un client l'utilisant
transport = AIOHTTPTransport(url=secret["url"] + '/graphql' + '?access_token=' + access_token)
client = Client(transport=transport, fetch_schema_from_transport=True)

############################################################################################
## INITIALISATION DU GRAPHE ET NAMESPACES
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

def make_E13(path, subject, predicate, object):
  E13_uri = she(cache.get_uuid(path, True))
  t(E13_uri, a, crm("E13_Attribute_Assignement"))
  t(E13_uri, crm("P14_carried_out_by"), she("684b4c1a-be76-474c-810e-0f5984b47921"))
  t(E13_uri, crm("P140_assigned_attribute_to"), subject)
  t(E13_uri, crm("P141_assigned"), object)
  t(E13_uri, crm("P177_assigned_property_type"), predicate)


############################################################################################
## DONNEES STATIQUES
############################################################################################

E32_lieux_uri = u(iremus_ns["947a38f0-34ac-4c54-aeb7-69c5f29e77c0"])
t(E32_lieux_uri, a, crm("E32_Authority_Document"))
t(E32_lieux_uri, crm("P1_is_identified_by"), l("Lieux"))

E52_GrandSiecle_uri = she(cache.get_uuid(["lieux", "E52 Grand Siècle"], True))
t(E52_GrandSiecle_uri, a, crm("E52_Time-Span"))
t(E52_GrandSiecle_uri, crm("P1_is_identified_by"), l("Grand Siècle"))

E52_MondeContemp_uri = she(cache.get_uuid(["lieux", "E52 Monde contemporain"], True))
t(E52_MondeContemp_uri, a, crm("E52_Time-Span"))
t(E52_MondeContemp_uri, crm("P1_is_identified_by"), l("Monde Contemporain"))

############################################################################################
## RECUPERATION DES DONNEES DANS DIRECTUS
############################################################################################

print("Récupération des données Directus…")

query = gql("""
query ($page_size: Int) {
	lieux(limit: 500, offset: $page_size) {
		id
		label
		parents {
		parent_id {
			id
		}
		}
		periode_historique
		note_historique
		alt_label_1
		alt_label_2
		etats_actuels {
			etat_actuel_id {
			id
			label
		}
		}
		fusions {
		fusion_id {
			id
			label
		}
		}
		cassini_alignement
		cassini_voir_aussi
		geonames_alignement
		geonames_voir_aussi
		coordonnees_geographiques
  }
}
""")

page_size = 0

while True:

	response = client.execute(query, variable_values= {"page_size": page_size} )

	#--------------------------------------------------------------------------------------
	# CREATION DES TRIPLETS
	#--------------------------------------------------------------------------------------

	print("    Création des triplets RDF…")
	
	for lieu in response["lieux"]:
	
		if lieu["label"] == "Grand Siècle" or lieu["label"] == "Monde contemporain":
			continue

		E93_uri = she(lieu["id"])
		t(E93_uri, a, crm("E93_Presence"))
		t(E32_lieux_uri, crm("P71_lists"), E93_uri)

		# PrefLabel
		E41_uri = she(cache.get_uuid(["lieux", E93_uri, "E41"], True))
		t(E93_uri, crm("P1_is_identified_by"), E41_uri)
		t(E41_uri, a, crm("E41_Appellation"))
		t(E41_uri, RDFS.label, l(lieu["label"]))
		t(E41_uri, crm("P2_has_type"), she("3cf0c743-ee9b-4dfc-8133-7dd383a1b6be"))

		# AltLabels
		n = 1
		clé = "alt_label_" + str(n)
		while clé in lieu.keys():
			altlabel = lieu[clé]
			if altlabel != None:
				E41_alt_uri = she(cache.get_uuid(["lieux", E93_uri, "E41 alt", altlabel], True))
				t(E41_alt_uri, a, crm("E41_Appellation"))
				t(E41_alt_uri, RDFS.label, l(altlabel))
				t(E93_uri, crm("P1_is_identified_by"), E41_alt_uri)
				t(E41_alt_uri, crm("P2_has_type"), she("70589b95-4156-431e-a58a-818af6dc795a"))
			n += 1
			clé = "alt_label_" + str(n)

		# Période historique
		if lieu["periode_historique"] == "grand_siecle":
			make_E13(["lieux", E93_uri, "E52 Grand Siècle", "E13"], E93_uri, crm("P4_has_time-span"), E52_GrandSiecle_uri)
		else:
			make_E13(["lieux", E93_uri, "E52 Monde Contemporain", "E13"], E93_uri, crm("P4_has_time-span"), E52_MondeContemp_uri)

		# Note historique
		if lieu["note_historique"] != None:

			make_E13(["lieux", E93_uri, "note historique", "E13"], E93_uri, crm("P3_has_note"), l(lieu["note_historique"]))


		# Alignements
		def alignement(champ, predicat):
			if lieu[champ] != None:
				try:
					url_alignement = lieu[champ].split("Identifiant")[0]
					url_alignement = url_alignement.replace("<a href='", '').replace("'>", "").replace(" ", "")
					t(E93_uri, predicat, u(url_alignement))
				except:
					print(lieu, lieu[champ], ": URI")
	

		alignement("cassini_alignement", SKOS.exactMatch)
		alignement("geonames_alignement", SKOS.exactMatch)
		alignement("cassini_voir_aussi", SKOS.closeMatch)
		alignement("geonames_voir_aussi", SKOS.closeMatch)

		# Parents
		if lieu["parents"] != None:
			for parent in lieu["parents"]:
				make_E13(["lieux", E93_uri, "parent", "E13"], E93_uri, crm("P10_falls_within"), she(parent["parent_id"]["id"]))

		# Etats actuels (E4_Period)
		def link_to_E4(uri, etat_actuel):
			make_E13(["lieux", uri, "E4", etat_actuel, "E13"], uri, crm("P166_was_a_presence_of"), E4_uri)

		if lieu["etats_actuels"] != None:
			for etat_actuel in lieu["etats_actuels"]:
				E4_label = etat_actuel["etat_actuel_id"]["label"] + " / " + lieu["label"]
				E4_uri = she(cache.get_uuid(["lieux", E93_uri, "E4", "uuid"], True))
				t(E4_uri, a, crm("E4_Period"))
				t(E4_uri, crm("is_identified_by"), l(E4_label))

				link_to_E4(E93_uri, etat_actuel)
				link_to_E4(she(etat_actuel["etat_actuel_id"]["id"]), etat_actuel)

		# Fusions
		if lieu["fusions"] != None:
			for fusion in lieu["fusions"]:
				fusion_uri = she(cache.get_uuid(["lieux", E93_uri, "fusion", "uuid"], True))
				t(fusion_uri, a, she_ns("Fusion"))
				make_E13(["lieux", E93_uri, "fusion", fusion, "E13 was merged"], E93_uri, she_ns("was_merged"), fusion_uri)
				make_E13(["lieux", E93_uri, "fusion", fusion, "E13 commune nouvelle"], fusion_uri, she_ns("commune_nouvelle"), E93_uri)
			

		# Coordonnées géographiques
		if lieu["coordonnees_geographiques"] != None:
			coordonnees = lieu["coordonnees_geographiques"]["coordinates"]
			coordonnees = str(coordonnees)[1:-1]
				
			E53_uri = she(cache.get_uuid(["lieux", E93_uri, "E53", "uuid"], True))
			t(E53_uri, a, crm("E53_Place"))
			t(E53_uri, crm("P168_place_is_defined_by"), l(coordonnees))

			make_E13(["lieux", E93_uri, "E53", "E13"], E93_uri, crm("P161_has_spatial_projection"), E53_uri)


	print(f"    {page_size}")
	page_size += 500

	if not response["lieux"]:
		break


############################################################################################
## SERIALISATION DU GRAPHE
############################################################################################

print(f"Sérialisation du graphe [{args.ttl}]")

serialization = output_graph.serialize(format="turtle", base="http://data-iremus.huma-num.fr/id/")
with open(args.ttl, "w+") as f:
	f.write(serialization)

cache.bye()