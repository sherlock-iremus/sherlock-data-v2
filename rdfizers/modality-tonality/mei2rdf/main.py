import argparse
from asyncio.format_helpers import _format_callback
import chardet
import json
from lxml import etree
import os
from pathlib import Path, PurePath
import requests
import sys
import yaml

from sherlockcachemanagement import Cache
from sherlock_xml import idize
from mei_beats import get_beats_data
from mei_sherlockizer import rdfize

parser = argparse.ArgumentParser()
parser.add_argument("--output_mei_folder")
parser.add_argument("--output_ttl_folder")
args = parser.parse_args()

Path(args.output_mei_folder).mkdir(0o755, True, True)
Path(args.output_ttl_folder).mkdir(0o755, True, True)

################################################################################
# DIRECTUS
################################################################################

print("Récupération des données Directus…")

# Secret YAML
file = open(os.path.join(sys.path[0], "secret.yaml"))
secret = yaml.full_load(file)
r = requests.post(secret["url"] + "/auth/login", json={"email": secret["email"], "password": secret["password"]})
access_token = r.json()['data']['access_token']
refresh_token = r.json()['data']['refresh_token']
file.close()

query = """
query {
  partitions(limit: -1) {
    id
    pre_sherlock_url 
  }
}
"""

r = requests.post(secret["url"] + '/graphql' + '?access_token=' + access_token, json={'query': query})
result = json.loads(r.text)

################################################################################
# DATA
################################################################################

for partition in result["data"]["partitions"]:
    uuid = partition["id"]
    mei_file = Path(args.output_mei_folder, uuid + ".mei")
    print(f"? {uuid} — {mei_file} ", end="")
    if True == mei_file.is_file():
        print(f"✔")
        continue

    print(f"⚙ …")

    f_content = requests.get(partition["pre_sherlock_url"]).content

    input_mei_file_encoding = chardet.detect(f_content)
    input_mei_file_doc = etree.fromstring(f_content)
    idized_input_mei_file_doc = idize(input_mei_file_doc)

    with open(PurePath(args.output_mei_folder, uuid + ".mei"), "wb") as f2:
        etree.ElementTree(idized_input_mei_file_doc).write(
            f2,
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True
        )

    beats_data = get_beats_data(idized_input_mei_file_doc)

    rdfize(
        "http://data-iremus.huma-num.fr/graph/mei",
        idized_input_mei_file_doc,
        uuid,
        beats_data["score_beats"],
        beats_data["elements"],
        PurePath(args.output_ttl_folder, uuid + ".ttl")
    )

print(f"{len(result['data']['partitions'])} partitions traitées.")
