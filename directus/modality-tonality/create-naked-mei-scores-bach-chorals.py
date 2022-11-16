import argparse
import glob
from lxml import etree
import os
from pprint import pprint
import requests
import sys
import yaml
import xml.etree.ElementTree as ET

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--directus_secret")
parser.add_argument("--mei_folder")
args = parser.parse_args()

print("Obtention d'un token d'authentification Directus…")
file = open(os.path.join(sys.path[0], args.directus_secret))
secret = yaml.full_load(file)
file.close()
r = requests.post("http://bases-iremus.huma-num.fr/directus-catalogue" + "/auth/login", json={"email": secret["email"], "password": secret["password"]})
access_token = r.json()["data"]["access_token"]
refresh_token = r.json()["data"]["refresh_token"]

mei_ns = {"tei": "http://www.music-encoding.org/ns/mei"}
xml_ns = {"xml": "http://www.w3.org/XML/1998/namespace"}

for f in glob.glob(args.mei_folder + '/*.mei'):
    mei_gh_url = "https://raw.githubusercontent.com/polifonia-project/tonalities_pilot/main/scores/Bach_Chorals/" + f.split("/")[-1]
    x = requests.get(f"http://bases-iremus.huma-num.fr/directus-catalogue/items/partitions?access_token={access_token}&filter[pre_sherlock_url][_eq]={mei_gh_url}")
    x = x.json()["data"]
    if len(x) == 0:
        payload = {
            "note": "Bach choral " + f.split("/")[-1].split(".")[0],
            "pre_sherlock_url": mei_gh_url,
            "type": "fichier_mei"
        }
        y = requests.post(f"http://bases-iremus.huma-num.fr/directus-catalogue/items/partitions?access_token={access_token}", json=payload)

    root = ET.fromstring(requests.get(mei_gh_url).content)
