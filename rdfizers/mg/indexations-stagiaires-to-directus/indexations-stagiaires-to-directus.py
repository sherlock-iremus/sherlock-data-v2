import argparse
import glob
import json
import os
from pprint import pprint
import re
import requests
from slugify import slugify
import uuid
import yaml


def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))

        return True
    except ValueError:
        return False


# Constants
BASE = "http://bases-iremus.huma-num.fr/directus-rar"

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--caca_folder")
parser.add_argument("--secret_file")
parser.add_argument("--data")
parser.add_argument("--skos_motsclefs_json_from_ot")
args = parser.parse_args()

# if not os.path.exists(args.data):
# print("Exploration de l'arborescence")

# data = {
#     "congrégations": {},
#     "corporations": {},
#     "institutions": {},
#     "lieux": {},
#     "mots-clefs": {},
#     "oeuvres citées": {},
#     "personnages": {},
#     "personnes": {},
# }

# def make_index(cat, article_id, v):
#     article_id = article_id.lower()
#     if article_id not in data[cat]:
#         data[cat][article_id] = []
#     if v not in data[cat][article_id]:
#         data[cat][article_id].append(v)

# files = glob.glob(f"{args.caca_folder}/**/*.txt", recursive=True)
# for file in files:
#     with open(file, encoding="utf-8") as content:
#         filename = file.split(os.sep)[-1]
#         foldername = file.split(os.sep)[-2]
#         content = content.read()
#         lines = content.split("\n")
#         article_id = filename[3:-8]
#         for line in lines:
#             line = line.replace("\\", "").replace("**", "").strip()
#             if line:
#                 if line.startswith("MG"):
#                     pass

#                 elif line.startswith("17"):
#                     pass

#                 elif line.startswith("mots clés"):
#                     v = line.replace("mots clés", "").strip()
#                     make_index("mots-clefs", article_id, v)

#                 elif line.startswith("lieux"):
#                     v = line.replace("lieux ", "").strip()
#                     match = re.compile("[\[]{1,2}([0-9]+)[\]]{1,2}").search(v)
#                     if match:
#                         v_int = int(match.group(1))
#                     else:
#                         v_int = int(v)
#                     make_index("lieux", article_id, v_int)

#                 elif line.startswith("personnes"):
#                     last_line_cat = "personnes"
#                     v = line.replace("personnes", "").strip()
#                     if v:
#                         match = re.compile("[\[]{1,2}(.+?)[\]]{1,2}").search(v)
#                         if match:
#                             v = match.group(1)
#                         try:
#                             v = int(v)
#                         except:
#                             pass
#                         make_index("personnes", article_id, v)

#                 elif line.startswith("personnages"):
#                     line = line.replace("personnages", "").strip()
#                     last_line_cat = "personnages"
#                     make_index("personnages", article_id, line)
#                     pass
#                 elif line.startswith("personnage"):
#                     line = line.replace("personnage", "").strip()
#                     last_line_cat = "personnages"
#                     make_index("personnages", article_id, line)
#                     pass

#                 elif line.startswith("institutions"):
#                     last_line_cat = "institutions"
#                     v = line.replace("institutions", "").strip()
#                     if v:
#                         match = re.compile("[\[]{1,2}(.+?)[\]]{1,2}").search(v)
#                         if match:
#                             v = match.group(1)
#                         try:
#                             v = int(v)
#                         except:
#                             pass
#                         make_index("institutions", article_id, v)

#                 elif line.startswith("corporation"):
#                     last_line_cat = "corporation"
#                     v = line.replace("corporation", "").strip()
#                     if v:
#                         match = re.compile("[\[]{1,2}(.+?)[\]]{1,2}").search(v)
#                         if match:
#                             v = match.group(1)
#                         try:
#                             v = int(v)
#                         except:
#                             pass
#                         make_index("corporations", article_id, v)

#                 elif line.startswith("congrégations"):
#                     last_line_cat = "congrégations"
#                     v = line.replace("congrégations", "").strip()
#                     if v:
#                         match = re.compile("[\[]{1,2}(.+?)[\]]{1,2}").search(v)
#                         if match:
#                             v = match.group(1)
#                         try:
#                             v = int(v)
#                         except:
#                             pass
#                         make_index("congrégations", article_id, v)

#                 elif line.startswith("oeuvre citée"):
#                     last_line_cat = "oeuvre citée"
#                     v = line.replace("oeuvre citée", "").strip()
#                     make_index("oeuvres citées", article_id, v)

#                 elif line[0] == '[':
#                     v = line.strip()
#                     if line:
#                         match = re.compile("[\[]{1,2}(.+?)[\]]{1,2}").search(v)
#                         if match:
#                             v = match.group(1)
#                         else:
#                             print("ERREUR", file.split("\\")[-1], line)
#                         try:
#                             v = int(v)
#                         except:
#                             pass
#                         make_index(last_line_cat, article_id, v)

#                 else:
#                     print("ERREUR", file.split("\\")[-1], line)
#                     pass

# with open(args.data, 'w', encoding='utf8') as outfile:
#     json.dump(data, outfile, ensure_ascii=False)

with open(args.data, 'r', encoding='utf8') as f:
    data = json.load(f)

print("Obtention du token d'accès à l'API Directus…")
file = open(args.secret_file)
secret = yaml.full_load(file)
file.close()
r = requests.post(BASE + "/auth/login", json={"email": secret["email"], "password": secret["password"]})
access_token = r.json()["data"]["access_token"]
refresh_token = r.json()["data"]["refresh_token"]

# print("INDEXATIONS PERSONNES")
# for article_id, ot_personnes_id in data["personnes"].items():
#     for ot_personne_id in ot_personnes_id:
#         if is_valid_uuid(ot_personne_id):
#             y = requests.post(f"{BASE}/items/indexations_articles_mg_personnes?access_token={access_token}", json={
#                 "id": str(uuid.uuid4()),
#                 "article_id": article_id,
#                 "personne_id": ot_personne_id
#             })
#             # print(y.json())
#         else:
#             x = requests.get(f"{BASE}/items/personnes?access_token={access_token}&filter[opentheso_id][_eq]={ot_personne_id}")
#             if len(x.json()["data"]) > 1:
#                 raise Exception("Plusieurs personnes ayant le même identifiant Opentheso ont été trouvées dans Directus !")
#             elif len(x.json()["data"]) == 0:
#                 print(f"[ERREUR] `personne` introuvable dans Directus (identifiant Opentheso invalide ?) : {ot_personne_id}")
#             else:

#                 y = requests.post(f"{BASE}/items/indexations_articles_mg_personnes?access_token={access_token}", json={
#                     "id": str(uuid.uuid4()),
#                     "article_id": article_id,
#                     "personne_id": x.json()["data"][0]["id"]
#                 })
#                 print(y.json())

# print("INDEXATIONS LIEUX")
# for article_id, ot_lieux_id in data["lieux"].items():
#     for ot_lieu_id in ot_lieux_id:
#         x = requests.get(f"{BASE}/items/lieux?access_token={access_token}&filter[opentheso_id][_eq]={ot_lieu_id}")
#         if len(x.json()["data"]) > 1:
#             raise Exception("Plusieurs lieux ayant le même identifiant Opentheso ont été trouvées dans Directus !")
#         elif len(x.json()["data"]) == 1:
#             y = requests.post(f"{BASE}/items/indexations_articles_mg_lieux?access_token={access_token}", json={
#                 "id": str(uuid.uuid4()),
#                 "article_id": article_id,
#                 "lieu_id": x.json()["data"][0]["id"]
#             })
#             print(y.json())
#         else:
#             print(f"[ERREUR] article {article_id} — lieu inexistant dans Directus {ot_lieu_id}")

print("INDEXATIONS MOTS-CLEFS")
if not os.path.exists(args.skos_motsclefs_json_from_ot):
    with open(args.skos_motsclefs_json_from_ot, 'w', encoding='utf8') as outfile:
        json.dump(requests.get("https://opentheso.huma-num.fr/opentheso/api/all/theso?id=th317&format=jsonld").json(), outfile, ensure_ascii=False)
with open(args.skos_motsclefs_json_from_ot, 'r', encoding='utf8') as f:
    skos_mc = json.load(f)
mc_slug2id = {}
for c in skos_mc:
    mc_id = c["http://purl.org/dc/terms/identifier"][0]["@value"]
    mc_preflabel = slugify(c["http://www.w3.org/2004/02/skos/core#prefLabel"][0]["@value"])
    mc_slug2id[mc_preflabel] = mc_id
for article_id, ot_mcs_id in data["mots-clefs"].items():
    for ot_mc_id in ot_mcs_id:
        ot_mc_id = slugify(ot_mc_id)
        if ot_mc_id not in mc_slug2id:
            print(article_id.ljust(15), ot_mc_id)
        else:
            x = requests.post(f"{BASE}/items/indexations_articles_mg_mots_clefs?access_token={access_token}", json={
                "id": str(uuid.uuid4()),
                "article_id": article_id,
                "mot_clef_id": mc_slug2id[ot_mc_id]
            })
