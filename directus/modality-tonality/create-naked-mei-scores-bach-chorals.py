import argparse
import glob
import os
import sys
import xml.etree.ElementTree as ET
from pprint import pprint

import requests
import yaml
from lxml import etree

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--directus_secret")
parser.add_argument("--mei_folder")
args = parser.parse_args()

BASE = "http://bases-iremus.huma-num.fr/directus-catalogue"
BACH_UUID = "265ba91d-ed61-4713-836f-3c1d68502618"

print("Obtention d'un token d'authentification Directus…")
file = open(os.path.join(sys.path[0], args.directus_secret))
secret = yaml.full_load(file)
file.close()
r = requests.post("http://bases-iremus.huma-num.fr/directus-catalogue" + "/auth/login", json={"email": secret["email"], "password": secret["password"]})
access_token = r.json()["data"]["access_token"]
refresh_token = r.json()["data"]["refresh_token"]

mei_ns = "{http://www.music-encoding.org/ns/mei}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"

for f in glob.glob(args.mei_folder + '/*.mei'):

    mei_gh_url = "https://raw.githubusercontent.com/polifonia-project/tonalities_pilot/main/scores/Bach_Chorals/" + f.split("/")[-1]

    # SCORE
    score_id = None
    x = requests.get(f"{BASE}/items/partitions?access_token={access_token}&filter[pre_sherlock_url][_eq]={mei_gh_url}")
    x = x.json()["data"]
    if len(x) == 0:
        payload = {
            "note": "Bach choral " + f.split("/")[-1].split(".")[0],
            "pre_sherlock_url": mei_gh_url,
            "type": "fichier_mei"
        }
        y = requests.post(f"{BASE}/items/partitions?access_token={access_token}", json=payload)
        score_id = y.json()["data"]["id"]
    else:
        score_id = x[0]["id"]

    # WORK
    root = ET.fromstring(requests.get(mei_gh_url).content)
    title = root.find(f".//{mei_ns}title").text
    title = title.replace("&auml;", "ä")
    title = title.replace("&uuml;", "ü")
    title = title.replace("&ouml;", "ö")
    title = title.strip()
    work_id = None
    x = requests.get(f"{BASE}/items/oeuvres?access_token={access_token}&filter[partitions][pre_sherlock_url][_eq]={mei_gh_url}")
    x = x.json()["data"]
    if len(x) == 0:
        y = requests.post(
            f"{BASE}/items/oeuvres?access_token={access_token}",
            json={
                "titre": title,
            }
        )
        work_id = y.json()["data"]["id"]
    else:
        work_id = x[0]["id"]

    # REL STUFF
    x = requests.patch(f"{BASE}/items/partitions/{score_id}?access_token={access_token}", json={
        "oeuvre": work_id
    })
    x = requests.get(f"{BASE}/items/oeuvres_compositeurs?access_token={access_token}&filter[compositeurs_id][_eq]={BACH_UUID}&filter[oeuvres_id][_eq]={work_id}")
    x = x.json()["data"]
    if len(x) == 0:
        y = requests.post(f"{BASE}/items/oeuvres_compositeurs?access_token={access_token}", json={
            "compositeurs_id": BACH_UUID,
            "oeuvres_id": work_id
        })
