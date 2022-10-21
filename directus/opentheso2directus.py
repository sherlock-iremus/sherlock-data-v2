import argparse
from attr import has
import json
from lxml import html
import os
from pprint import pprint
from rdflib import DCTERMS, Graph, RDF, SKOS
import re
import requests
import sys
from urllib.parse import urlparse
from urllib.parse import parse_qs
import xml.etree.ElementTree as ET
import yaml

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--skos_jsonld_file")
parser.add_argument("--skos_jsonld_api")
parser.add_argument("--directus_secret")
parser.add_argument("--directus_url")
parser.add_argument("--directus_collection")
args = parser.parse_args()

print("Récupération des données SKOS…")
skos_data = {}
if args.skos_jsonld_file:
    with open(args.skos_jsonld_file) as f:
        skos_data = json.loads(f.read())
else:
    r = requests.get(args.skos_jsonld_api, stream=True)
    skos_data = json.loads(r.text)

print("Analyse des données SKOS…")

narrowers = {}
broaders = {}
skos_directus_data = {}


def census(broader, narrower):
    if broader not in narrowers:
        narrowers[broader] = set()
    narrowers[broader].add(narrower)
    if narrower not in broaders:
        broaders[narrower] = set()
    broaders[narrower].add(broader)


print("Création des labels des broaders…")

for x in skos_data:
    skos_directus_data[x["@id"]] = {
        "uuid": x["http://purl.org/dc/terms/identifier"][0]["@value"].strip(),
        "preflabel": x["http://www.w3.org/2004/02/skos/core#prefLabel"][0]["@value"].strip()
    }
    if "http://www.w3.org/2004/02/skos/core#narrower" in x:
        for narrower in x["http://www.w3.org/2004/02/skos/core#narrower"]:
            census(x["@id"], narrower["@id"])
    if "http://www.w3.org/2004/02/skos/core#broader" in x:
        for broader in x["http://www.w3.org/2004/02/skos/core#broader"]:
            census(broader["@id"], x["@id"])


def make_ancestors(concept):
    ancestors = {}
    if concept in broaders:
        for broader in broaders[concept]:
            ancestors[skos_directus_data[broader]["preflabel"]] = make_ancestors(broader)
    return ancestors


def make_ancestors_paths(ancestors):
    def paths(tree, cur=()):
        if not tree:
            yield cur
        else:
            for n, s in tree.items():
                for path in paths(s, cur+(n,)):
                    yield path
    return " 🟣 ".join(map(
        lambda x: "/".join(x),
        map(
            lambda x: list(reversed(x)),
            paths(ancestors)
        )
    ))


for concept in skos_directus_data:
    ancestors = make_ancestors_paths(make_ancestors(concept))
    skos_directus_data[concept]["broaders"] = ancestors

print("Obtention d'un token d'authentification Directus…")
file = open(os.path.join(sys.path[0], args.directus_secret))
secret = yaml.full_load(file)
file.close()
r = requests.post(args.directus_url + "/auth/login", json={"email": secret["email"], "password": secret["password"]})
access_token = r.json()["data"]["access_token"]
refresh_token = r.json()["data"]["refresh_token"]


def print_response(r):
    print(f"{r.request.method} {r.status_code} {r.request.path_url.split('?')[0]}")


print(f"Création de la collection… [{args.directus_collection}]")
r = requests.post(f"{args.directus_url}/collections?access_token={access_token}", json={
    "collection": "thesaurus_opentheso",
    "meta": {
        "collection": "thesaurus_opentheso",
        "icon": "folder"
    }
})
print_response(r)
r = requests.get(f"{args.directus_url}/collections/{args.directus_collection}?access_token={access_token}")
print_response(r)
if r.status_code != 403:
    # Clear all items
    r = requests.get(f"{args.directus_url}/items/{args.directus_collection}?access_token={access_token}&limit=-1")
    all_id = list(map(lambda x: x["id"], r.json()["data"]))
    r = requests.delete(f"{args.directus_url}/items/{args.directus_collection}?access_token={access_token}", json=all_id)
    print_response(r)
    # Delete collection
    r = requests.delete(f"{args.directus_url}/collections/{args.directus_collection}?access_token={access_token}")
    print_response(r)
r = requests.post(f"{args.directus_url}/collections?access_token={access_token}", json={
    "collection": args.directus_collection,
    "meta": {
        "collection": args.directus_collection,
        "icon": "tag",
        "group": "thesaurus_opentheso",
        "note": "Cache Opentheso"
    },
    "schema": {},
    "fields": [
        {"field": "id", "type": "string", "meta": {"special": "uuid"}, "schema": {"is_primary_key": True}},
        {"field": "preflabel", "type": "string"},
        {"field": "broaders", "type": "text"}
    ]
})
print_response(r)

print("Insertion des items…")
i = 1
for id, concept in skos_directus_data.items():
    r = requests.post(f"{args.directus_url}/items/{args.directus_collection}?access_token={access_token}", json={
        "id": concept["uuid"],
        "preflabel": concept["preflabel"],
        "broaders": concept["broaders"]
    })
    print(f"{str(i).zfill(len(str(len(skos_directus_data))))}/{len(skos_directus_data)}")
    i += 1
