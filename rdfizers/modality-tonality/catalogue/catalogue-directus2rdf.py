import argparse
from datetime import datetime
from pprint import pprint
from rdflib import Graph, Literal, Namespace, URIRef
import requests
import yaml

from sherlockcachemanagement import Cache

# Args
parser = argparse.ArgumentParser()
parser.add_argument("--ttl")
parser.add_argument("--cache")
parser.add_argument("--secret")
args = parser.parse_args()

# Constantes
BASE_URI = f"http://bases-iremus.huma-num.fr/directus-catalogue"
E55_PRENOM = URIRef("bb483a36-1f03-43b5-9793-402bc9ce5ea2")
E55_NOM = URIRef("bb483a36-1f03-43b5-9793-402bc9ce5ea2")
base = Namespace("http://data-iremus.huma-num.fr/id/")
crm_ns = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
crmdig_ns = Namespace("")
sherlock_ns = Namespace("http://data-iremus.huma-num.fr/ns/sherlock#")
sherlockmei_ns = Namespace("http://data-iremus.huma-num.fr/ns/sherlockmei#")

# Init
cache = Cache(args.cache)
g = Graph()

# Secret YAML
file = open(args.secret)
secret = yaml.full_load(file)
r = requests.post(BASE_URI + "/auth/login", json={"email": secret["email"], "password": secret["password"]})
access_token = r.json()['data']['access_token']
refresh_token = r.json()['data']['refresh_token']
file.close()
param_at = f"access_token={access_token}"

# Compositeurs
print("COMPOSITEURS", end="")
r = requests.get(f"{BASE_URI}/items/compositeurs?{param_at}")
compositeurs = r.json()["data"]
print(f" : {len(compositeurs)} items")
for compositeur in compositeurs:
    uuid = compositeur["id"]
    nom = compositeur["nom"]
    prenom = compositeur["prenom"]
    pseudonyme = compositeur["pseudonyme"]
    annee_deces_max = compositeur["annee_deces_max"]
    annee_deces_min = compositeur["annee_deces_min"]
    annee_naissance_max = compositeur["annee_naissance_max"]
    annee_naissance_min = compositeur["annee_naissance_min"]
    
    e41_nom_uuid = cache.get_uuid(["compositeurs", uuid, "e41_nom", "uuid"], True)
    e41_prenom_uuid = cache.get_uuid(["compositeurs", uuid, "e41_prenom", "uuid"], True)
    print(uuid, e41_nom_uuid)

# That's all folks!
cache.bye()
serialization = g.serialize(format='turtle', base="http://data-iremus.huma-num.fr/id/")
with open(args.ttl, "w+") as f:
    f.write(serialization)
