import argparse
from attr import has
from lxml import html
import os
from pprint import pprint
from rdflib import Graph, SKOS, DCTERMS
import re
import requests
import sys
from urllib.parse import urlparse
from urllib.parse import parse_qs
import yaml

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--skos")
parser.add_argument("--skos_cache")
args = parser.parse_args()

# Secret YAML pour les requêtes Directus
print("Obtention du token d'accès à l'API Directus…")
file = open(os.path.join(sys.path[0], "secret.yaml"))
secret = yaml.full_load(file)
r = requests.post(secret["url"] + "/auth/login", json={"email": secret["email"], "password": secret["password"]})
access_token = r.json()["data"]["access_token"]
refresh_token = r.json()["data"]["refresh_token"]
file.close()
API = f"http://bases-iremus.huma-num.fr/directus-rar/items/lieux?access_token={access_token}"
API_LIEUX_ASSOCIATIONS = f"http://bases-iremus.huma-num.fr/directus-rar/items/lieux_associations?access_token={access_token}"
API_LIEUX_PARENTS_ENFANTS = f"http://bases-iremus.huma-num.fr/directus-rar/items/lieux_parents_enfants?access_token={access_token}"
API_SOURCES_ARTICLES_LIEUX = f"http://bases-iremus.huma-num.fr/directus-rar/items/sources_articles_lieux?access_token={access_token}"
API_SOURCES_ARTICLES = f"http://bases-iremus.huma-num.fr/directus-rar/items/sources_articles?access_token={access_token}"
def API_GET_LIEU_BY_ID(id): return f"http://bases-iremus.huma-num.fr/directus-rar/items/lieux/{id}?access_token={access_token}"
def API_GET_LIEUX_ASSOCIATIONS(lieu_1_uuid, lieu_2_uuid): return f"http://bases-iremus.huma-num.fr/directus-rar/items/lieux_associations?access_token={access_token}&filter[lieu_1_id][_eq]={lieu_1_uuid}&filter[lieu_2_id][_eq]={lieu_2_uuid}"
def API_GET_PARENTS_ENFANTS(parent_uuid, enfant_uuid): return f"http://bases-iremus.huma-num.fr/directus-rar/items/lieux_parents_enfants?access_token={access_token}&filter[parent_id][_eq]={parent_uuid}&filter[enfant_id][_eq]={enfant_uuid}"
def API_GET_SOURCES_ARTICLES_LIEUX(article_id, lieu_uuid): return f"http://bases-iremus.huma-num.fr/directus-rar/items/sources_articles_lieux?access_token={access_token}&filter[source_article_id][_eq]={article_id}&filter[lieu_id][_eq]={lieu_uuid}"


# Graph
print("Chargement des données SKOS…")
g = Graph()
g.parse(args.skos)

################################################################################
# HELPERS
################################################################################


def clean(s):
    s = str(s)
    s = " ".join(map(lambda x: x.strip(), s.split("\n")))
    s = s.replace('  ', ' ')
    return s


def fuckTags(s):
    try:
        tree = html.fromstring(s)
        s = tree.text_content().strip()
        return s
    except:
        return " "


def index(lieu, mg):
    if lieu not in indexations:
        indexations[lieu] = set()
    indexations[lieu].add(mg)


def extract_indices(s):
    return list(
        map(
            lambda x: 'MG-' + x.replace('MG-', '').lower(),
            filter(
                lambda x: re.search('[0-9]', x),
                map(
                    lambda x: x.strip(), s.split("##")
                )
            )
        )
    )


def extract_id(url):
    parsed_qs = parse_qs(urlparse(url).query)
    return int(parsed_qs["idc"][0])

################################################################################
# STRUCTURES
################################################################################


lieux = {}
indexations = {}
tree = {}
related = {}

skos_cache = {}
if os.path.exists(args.skos_cache):
    file = open(fr"{args.skos_cache}")
    skos_cache = yaml.full_load(file)
    file.close()
for p in ["id_uuid", "periodes_historiques", "uuid_id"]:
    if p not in skos_cache:
        skos_cache[p] = {}

################################################################################
# PROCESS
################################################################################

print("Exploration des données SKOS…")

for s, p, o in g:
    parsed_qs = parse_qs(urlparse(s).query)
    if "idc" in parsed_qs and "idt" in parsed_qs:

        # ID
        id = extract_id(s)
        if id not in lieux:
            lieux[id] = {}
        lieux[id]["opentheso_id"] = id

        # Période historique
        if p == DCTERMS.description:
            periode = str(o)[:4]
            if periode == "1336":
                lieux[id]["periode_historique"] = "grand_siecle"
            else:
                lieux[id]["periode_historique"] = "monde_contemporain"
            skos_cache["periodes_historiques"][id] = lieux[id]["periode_historique"]

        # Définition
        if p == SKOS.definition:
            lieux[id]["definition"] = str(o)

        # Coordonnées
        if str(p) == "http://www.w3.org/2003/01/geo/wgs84_pos#lat":
            lieux[id]["lat"] = float(o)
        if str(p) == "http://www.w3.org/2003/01/geo/wgs84_pos#long":
            lieux[id]["long"] = float(o)

        # Labels
        if p == SKOS.prefLabel:
            lieux[id]["label"] = clean(o)
        if p == SKOS.altLabel:
            if "alt_labels" not in lieux[id]:
                lieux[id]["alt_labels"] = {}
            lieux[id]["alt_labels"]["alt_label_" + str(1 + len(lieux[id]["alt_labels"].items()))] = clean(o)

        # Notes & Indexations
        if p == SKOS.historyNote:
            lieux[id]["note_historique"] = fuckTags(clean(o))
        if p == SKOS.scopeNote:
            note_1 = fuckTags(clean(o))
            if "##" in note_1:
                for i in extract_indices(note_1):
                    index(id, i)
            else:
                lieux[id]["note_1"] = note_1
        if p == SKOS.note:
            note_2 = fuckTags(clean(o))
            if "##" in note_2:
                for i in extract_indices(note_2):
                    index(id, i)
            else:
                lieux[id]["note_2"] = note_2
        if p == SKOS.editorialNote:
            note_3 = fuckTags(clean(o))
            lieux[id]["note_3"] = note_3

        # Match
        if p == SKOS.exactMatch:
            if "cassini" in o:
                lieux[id]["cassini_alignement"] = str(o)
            elif "geonames" in o:
                lieux[id]["geonames_alignement"] = str(o)
            elif "data.bnf.fr" in o:
                lieux[id]["data_bnf_alignement"] = str(o)
        if p == SKOS.closeMatch:
            if "cassini" in o:
                lieux[id]["cassini_voir_aussi"] = str(o)
            elif "geonames" in o:
                lieux[id]["geonames_voir_aussi"] = str(o)
            elif "data.bnf.fr" in o:
                lieux[id]["data_bnf_voir_aussi"] = str(o)

        # Narrower/Broader
        if p == SKOS.narrower:
            if id not in tree:
                tree[id] = set()
            tree[id].add(extract_id(o))
        if p == SKOS.broader:
            broader = extract_id(o)
            if broader not in tree:
                tree[broader] = set()
            tree[broader].add(id)

        # Related
        if p == SKOS.related:
            if id not in related:
                related[id] = set()
            related[id].add(extract_id(o))

print("Reformatage des données…")

for id, lieu in lieux.items():
    if "alt_labels" in lieu:
        for k, v in lieu["alt_labels"].items():
            lieu[k] = v
        del lieu["alt_labels"]
    if "lat" in lieu and "long" in lieu:
        lieu["coordonnees_geographiques"] = {"coordinates": [lieu["long"], lieu["lat"]], "type": "Point"}
        del lieu["lat"]
        del lieu["long"]

print("Envoi des données à Directus…")

if False:
    i = 0
    for id, lieu in lieux.items():
        i += 1
        x = requests.get(f"{API}&filter[opentheso_id][_eq]={id}")
        x = x.json()["data"]
        if 0 == len(x):
            y = requests.post(f"{API}", json=lieu)
            print(f"{i}/{len(lieux.items())}".ljust(10) + " POST  " + str(id))
        else:
            y = requests.patch(f"{API}", json=lieu)
            print(f"{i}/{len(lieux.items())}".ljust(10) + " PATCH " + str(id))

print("Constitution du cache d'identifiants UUID Directus/ID Opentheso…")

i = 0
if len(skos_cache["id_uuid"]) == 0 and len(skos_cache["uuid_id"]) == 0:
    for id, lieu in lieux.items():
        x = requests.get(f"{API}&filter[opentheso_id][_eq]={id}")
        uuid = x.json()["data"][0]["id"]
        skos_cache["uuid_id"][uuid] = id
        skos_cache["id_uuid"][id] = uuid
        i += 1
        print(i)

print("Traitement des relations SKOS.narrower/SKOS.broader…")

if False:
    n_relations_parent_enfant = 0
    for parent_opentheso_id, enfants in tree.items():
        n_relations_parent_enfant += len(enfants)
    i = 1

    for parent_opentheso_id, enfants in tree.items():
        parent_uuid = skos_cache["id_uuid"][parent_opentheso_id]
        for enfant_opentheso_id in enfants:
            try:
                enfant_uuid = skos_cache["id_uuid"][enfant_opentheso_id]
                x = requests.get(API_GET_PARENTS_ENFANTS(parent_uuid, enfant_uuid)).json()["data"]
                if len(x) == 0:
                    y = requests.post(API_LIEUX_PARENTS_ENFANTS, json={
                        "parent_id": parent_uuid,
                        "enfant_id": enfant_uuid
                    })
                    print(f"POST {parent_uuid} {enfant_uuid} {i}/{n_relations_parent_enfant}")
                else:
                    print(f"EXIS {parent_uuid} {enfant_uuid} {i}/{n_relations_parent_enfant}")
            except Exception as e:
                print(e)
                print(f"Identifiant opentheso invalide : {enfant_opentheso_id}")
            i += 1

print("Traitement des relations SKOS.related…")

if False:
    for lieu_opentheso_id, lieux_associés in related.items():
        lieu_uuid = skos_cache["id_uuid"][lieu_opentheso_id]
        for lieu_associé_opentheso_id in lieux_associés:
            lieu_associé_uuid = skos_cache["id_uuid"][lieu_associé_opentheso_id]

            x = requests.get(API_GET_LIEUX_ASSOCIATIONS(lieu_uuid, lieu_associé_uuid)).json()["data"]
            if len(x) == 0:
                y = requests.post(API_LIEUX_ASSOCIATIONS, json={
                    "lieu_1_id": lieu_uuid,
                    "lieu_2_id": lieu_associé_uuid
                })

print("Traitement des indexations…")

if False:
    l_max = 0
    for k, v in indexations.items():
        l_max += len(v)
    l = 1

    for lieu_opentheso_id, articles_id in indexations.items():
        lieu_uuid = skos_cache["id_uuid"][lieu_opentheso_id]
        for article_id in articles_id:
            x = requests.get(API_GET_SOURCES_ARTICLES_LIEUX(article_id, lieu_uuid)).json()["data"]
            if len(x) == 0:
                y = requests.post(API_SOURCES_ARTICLES, json={"id": article_id})
                y = requests.post(API_SOURCES_ARTICLES_LIEUX, json={
                    "source_article_id": article_id,
                    "lieu_id": lieu_uuid
                })
            print(f"{lieu_uuid} {article_id.ljust(17)} {l}/{l_max}")
            l += 1

print("That's all folks…")

with open(fr"{args.skos_cache}", 'w') as file:
    yaml.dump(skos_cache, file)

# Lieux créés par l'admin :
# DELETE FROM lieux WHERE user_created = '5064230e-5ca1-4d3a-a9ef-0f94ef4c737d' ;
