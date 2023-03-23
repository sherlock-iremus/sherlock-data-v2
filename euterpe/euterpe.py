# python3 euterpe.py --xlsx_taxonomies sources/euterpe/euterpe_taxonomies.xlsx --xlsx_data sources/euterpe/euterpe_data.xlsx --cache caches/euterpe.yaml --skos_dir out/ttl/euterpe/skos

import argparse
import os
from pathlib import Path
from pprint import pprint
import requests
from rdflib import DCTERMS, Graph, Literal, Namespace, RDF, SKOS
from slugify import slugify
import sys
import yaml

################################################################################
# SETUP
################################################################################

BASE = "http://bases-iremus.huma-num.fr/directus-catalogue"

parser = argparse.ArgumentParser()
parser.add_argument("--step")
parser.add_argument("--xlsx_data")
parser.add_argument("--xlsx_taxonomies")
parser.add_argument("--cache")
parser.add_argument("--skos_dir")
parser.add_argument("--directus_secret")
args = parser.parse_args()

sys.path.append(os.path.abspath(os.path.join('../python_packages/helpers_excel', '')))
from helpers_excel import *  # nopep8
from sherlockcachemanagement import Cache  # nopep8

cache = Cache(args.cache)

print("Obtention d'un token d'authentification Directus…")
file = open(os.path.join(sys.path[0], args.directus_secret))
secret = yaml.full_load(file)
file.close()
r = requests.post(BASE + "/auth/login", json={"email": secret["email"], "password": secret["password"]})
access_token = r.json()["data"]["access_token"]
refresh_token = r.json()["data"]["refresh_token"]

################################################################################
# HELPERS
################################################################################


def rc(cell):
    cell = str(cell)
    cell = cell.strip()
    return cell


def get_databnf_entity_bt_foafname(x):
    q = """
        SELECT ?s
        WHERE {
            ?s <http://xmlns.com/foaf/0.1/name> \""""+x+"""\" .
        }
    """
    r = requests.post("https://data.bnf.fr/sparql", headers={"Accept": "application/json"}, data={"query": q})

    return r.json()["results"]["bindings"]


def get_concepts_uuid(taxonomy_name, string):
    if not string:
        return []

    strings = string.split("🍄")
    strings = [x.strip() for x in strings]

    return [cache.get_uuid(["taxonomies", taxonomy_name, "concepts", x or concept["name"], "uuid"]) for x in strings]


def directus_insert(collection, paylod):
    r = requests.post(f"{BASE}/items/{collection}?access_token={access_token}", json=payload)
    if "errors" in r.json() and r.json()["errors"][0]["extensions"]["code"] == 'RECORD_NOT_UNIQUE':
        r = requests.patch(f"{BASE}/items/{collection}/{id}?access_token={access_token}", json=payload)


def post_data(collection, payloads):
    r = requests.post(f"{BASE}/items/{collection}?access_token={access_token}&limit=-1", json=payloads)


################################################################################
# TAXONOMIES
################################################################################


if args.step == "taxonomies":

    taxonomies_data = get_xlsx_rows_as_dicts(args.xlsx_taxonomies)

    for taxonomy_name, taxonomy_data in taxonomies_data.items():

        # Init graph
        g = Graph()
        ns_opentheso = Namespace("https://opentheso.huma-num.fr/opentheso/")
        g.bind("dctrerms", DCTERMS)
        g.bind("opentheso", ns_opentheso)
        g.bind("skos", SKOS)

        skos_conceptscheme_uuid = cache.get_uuid(["taxonomies", taxonomy_name, "skos:ConceptScheme", "uuid"], True)
        g.add((ns_opentheso[skos_conceptscheme_uuid], RDF.type, SKOS.ConceptScheme))
        g.add((ns_opentheso[skos_conceptscheme_uuid], SKOS.prefLabel, Literal(taxonomy_name, "fr")))
        g.add((ns_opentheso[skos_conceptscheme_uuid], DCTERMS.identifier, Literal(skos_conceptscheme_uuid)))

        # Explore legacy data
        for concept in taxonomy_data:
            if not concept["id"] and not concept["name"]:
                continue

            skos_concept_uuid = cache.get_uuid(["taxonomies", taxonomy_name, "concepts", concept["id"] or concept["name"], "uuid"], True)
            skos_concept_uuid = concept["uuid"]
            g.add((ns_opentheso[skos_conceptscheme_uuid], SKOS.hasTopConcept, ns_opentheso[skos_concept_uuid]))
            g.add((ns_opentheso[skos_concept_uuid], RDF.type, SKOS.Concept))
            g.add((ns_opentheso[skos_concept_uuid], DCTERMS.identifier, Literal(skos_concept_uuid)))
            g.add((ns_opentheso[skos_concept_uuid], SKOS.prefLabel, Literal(concept["name"], "fr")))
            g.add((ns_opentheso[skos_concept_uuid], SKOS.inScheme, ns_opentheso[skos_conceptscheme_uuid]))

        # Serialize graph
        serialization = g.serialize(format="turtle")
        with open(Path(args.skos_dir, slugify(taxonomy_name)+".skos"), "w+", encoding="utf8") as f:
            f.write(serialization)

################################################################################
# AUTEURS
################################################################################


euterpe_data = get_xlsx_rows_as_dicts(args.xlsx_data)

check_alignements_bnf = True
alignements_bnf = {}
with open(r'alignements_bnf.yaml') as f:
    data = yaml.full_load(f)
    if data:
        check_alignements_bnf = False
        alignements_bnf = data

auteurs_payloads = []

for auteur in euterpe_data["1_auteurs"]:
    auteur = dict1_keys = {k: v.strip() if type(v) is str else v for (k, v) in auteur.items()}

    # pprint(auteur)

    nom_uuid = cache.get_uuid(["auteurs", auteur["uuid"], "nom", "uuid"], True)

    payload = {
        "id": auteur["uuid"],
        "vedette": auteur["nom"],
        "appellations": [
            {
                "id": nom_uuid,
                "libelle": auteur["nom"],
                "type": "51acf586-644e-4b25-b5ca-555cd791b727"  # Nom anagraphique
            }
        ]
    }

    if auteur["alias"]:
        aliases = [x.strip() for x in auteur["alias"].split("🍄")]
        for alias in aliases:
            alias_uuid = cache.get_uuid(["auteurs", auteur["uuid"], "aliases", alias, "uuid"], True)
            payload["appellations"].append({
                "id": alias_uuid,
                "libelle": alias,
                "type": "3edb57bb-a6ac-4809-a769-7c69be2f2c4c"  # Alias
            })

    if auteur["uuid"] in alignements_bnf:
        alignement_bnf_uuid = cache.get_uuid(["auteurs", auteur["uuid"], "alignements", "bnf", "uuid"], True)
        payload["alignements"] = [{
            "id": alignement_bnf_uuid,
            "iri": alignements_bnf[auteur["uuid"]]
        }]

    auteurs_payloads.append(payload)

    # Alignement BnF
    if check_alignements_bnf:
        parts = auteur["nom"].split(",")
        if 2 == len(parts):
            nom = (parts[1] + " " + parts[0]).lower().title().strip()
            print(auteur["uuid"], auteur["nom"], "=>", nom)
            r = get_databnf_entity_bt_foafname(nom)
            if len(r) == 1:
                alignements_bnf[auteur["uuid"]] = r[0]["s"]["value"]

with open('alignements_bnf.yaml', 'w') as f:
    yaml.dump(alignements_bnf, f)

post_data("personnes", auteurs_payloads)

################################################################################
# THAT'S ALL FOLKS!
################################################################################

cache.bye()
