import argparse
from attr import has
import glob
from lxml import html
import os
from pprint import pprint
from rdflib import Graph, SKOS, DCTERMS
import re
import requests
from striprtf.striprtf import rtf_to_text
import sys
from urllib.parse import urlparse
from urllib.parse import parse_qs
import yaml

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--lieux_skos_cache")
parser.add_argument("--caca_folder")
args = parser.parse_args()

# Secret YAML pour les requêtes Directus
print("Obtention du token d'accès à l'API Directus…")
file = open(os.path.join(sys.path[0], "secret.yaml"))
secret = yaml.full_load(file)
r = requests.post(secret["url"] + "/auth/login", json={"email": secret["email"], "password": secret["password"]})
access_token = r.json()["data"]["access_token"]
refresh_token = r.json()["data"]["refresh_token"]
file.close()

print("Construction du cache Opentheso [https://opentheso.huma-num.fr/opentheso/api/all/theso?id=th317&format=jsonld]")

# TODO

print("Exploration de l'arborescence•")

files = glob.glob(f"{args.caca_folder}/**/*.rtf", recursive=True)
for file in files:
    print(file)
    with open(file, encoding="cp1252") as content:
        content = content.read()
        content = rtf_to_text(content, errors="ignore")
        # print(content)
    # print("*"*120)
