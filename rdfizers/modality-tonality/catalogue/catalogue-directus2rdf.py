import argparse
from datetime import datetime
from pprint import pprint
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD
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
E55_PSEUDONYME = URIRef("78930375-9d85-43aa-8a1a-f458fcdbdfd0")
DOREMUS_COMPOSER = URIRef("http://data.doremus.org/vocabulary/function/composer")
crm_ns = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
crmdig_ns = Namespace("http://www.ics.forth.gr/isl/CRMdig/")
doremus_ns = Namespace("http://data.doremus.org/ontology#")
lrmoo_ns = Namespace("http://www.cidoc-crm.org/lrmoo/")
sherlock_ns = Namespace("http://data-iremus.huma-num.fr/ns/sherlock#")
sherlockmei_ns = Namespace("http://data-iremus.huma-num.fr/ns/sherlockmei#")
EOTB = crm_ns["P81a_end_of_the_begin"]
BOTE = crm_ns["P81b_begin_of_the_end"]
BOTB = crm_ns["P82a_begin_of_the_begin"]
EOTE = crm_ns["P82b_end_of_the_end"]

# Init
cache = Cache(args.cache)
g = Graph()
g.bind("crm", crm_ns)
g.bind("crmdig", crmdig_ns)
g.bind("doremus", doremus_ns)
g.bind("lrmoo", lrmoo_ns)
g.bind("sherlockns", sherlock_ns)
g.bind("sherlockmei", sherlockmei_ns)

# Secret YAML
file = open(args.secret)
secret = yaml.full_load(file)
r = requests.post(
    BASE_URI + "/auth/login",
    json={"email": secret["email"], "password": secret["password"]},
)
access_token = r.json()["data"]["access_token"]
refresh_token = r.json()["data"]["refresh_token"]
file.close()
param_at = f"access_token={access_token}"

print("COMPOSITEURS", end="")
compositeurs = requests.get(f"{BASE_URI}/items/compositeurs?{param_at}&limit=-1").json()["data"]
print(f" ({len(compositeurs)})")
for c in compositeurs:
    print("    ", c['id'], "", end="")
    print(f"[{c['annee_naissance_min'] or '····'}—{c['annee_naissance_max'] or '····'}/{c['annee_deces_min'] or '····'}—{c['annee_deces_max'] or '····'}] ".ljust(22), end="")
    print(f"{c['prenom']} {c['nom']} {('('+c['pseudonyme']+') ') if c['pseudonyme'] else ''}")
    compositeur_uuid = c["id"]
    compositeur = URIRef(compositeur_uuid)

    # Compositeur
    g.add((compositeur, RDF.type, crm_ns["E21_Person"]))

    # Nom
    if c["nom"]:
        e41_nom = URIRef(cache.get_uuid(["compositeurs", compositeur_uuid, "e41_nom", "uuid"], True))
        g.add((e41_nom, RDF.type, crm_ns["E41_Appellation"]))
        g.add((compositeur, crm_ns["P1_is_identified_by"], e41_nom))
        g.add((e41_nom, crm_ns["P2_has_type"], E55_NOM))
        g.add((e41_nom, crm_ns["P190_has_symbolic_content"], Literal(c["nom"])))

    # Prénom
    if c["prenom"]:
        e41_prénom = URIRef(cache.get_uuid(["compositeurs", compositeur_uuid, "e41_prénom", "uuid"], True))
        g.add((e41_prénom, RDF.type, crm_ns["E41_Appellation"]))
        g.add((compositeur, crm_ns["P1_is_identified_by"], e41_prénom))
        g.add((e41_prénom, crm_ns["P2_has_type"], E55_PRENOM))
        g.add((e41_prénom, crm_ns["P190_has_symbolic_content"], Literal(c["prenom"])))

    # Pseudonyme
    if c["pseudonyme"]:
        e41_pseudonyme = URIRef(cache.get_uuid(["compositeurs", compositeur_uuid, "e41_pseudonyme", "uuid"], True))
        g.add((e41_pseudonyme, RDF.type, crm_ns["E41_Appellation"]))
        g.add((compositeur, crm_ns["P1_is_identified_by"], e41_pseudonyme))
        g.add((e41_pseudonyme, crm_ns["P2_has_type"], E55_PSEUDONYME))
        g.add((e41_pseudonyme, crm_ns["P190_has_symbolic_content"], Literal(c["pseudonyme"])))

    # Naissance
    if c["annee_naissance_min"] or c["annee_naissance_max"]:
        e67 = URIRef(cache.get_uuid(["compositeurs", compositeur_uuid, "e67", "uuid"], True))
        g.add((e67, RDF.type, crm_ns["E67_Birth"]))
        e67_e52 = URIRef(cache.get_uuid(["compositeurs", compositeur_uuid, "e67", "e52", "uuid"], True))
        g.add((e67_e52, RDF.type, crm_ns["E52_Time-Span"]))
        g.add((e67, crm_ns["P98_brought_into_life"], compositeur))
        g.add((e67, crm_ns["P4_has_time-span"], e67_e52))
        if c["annee_naissance_min"]:
            g.add((e67_e52, BOTB, Literal(datetime(c["annee_naissance_min"], 1, 1), datatype=XSD.date)))
        if c["annee_naissance_max"]:
            g.add((e67_e52, EOTB, Literal(datetime(c["annee_naissance_max"], 12, 31), datatype=XSD.date)))

    # Mort
    if c["annee_deces_min"] or c["annee_deces_max"]:
        e69 = URIRef(cache.get_uuid(["compositeurs", compositeur_uuid, "e69", "uuid"], True))
        g.add((e69, RDF.type, crm_ns["E69_Death"]))
        e69_e52 = URIRef(cache.get_uuid(["compositeurs", compositeur_uuid, "e69", "e52", "uuid"], True))
        g.add((e69_e52, RDF.type, crm_ns["E52_Time-Span"]))
        g.add((e69, crm_ns["P100_was_death_of"], compositeur))
        g.add((e69, crm_ns["P4_has_time-span"], e69_e52))
        if c["annee_deces_min"]:
            g.add((e69_e52, BOTB, Literal(datetime(c["annee_deces_min"], 1, 1), datatype=XSD.date)))
        if c["annee_deces_max"]:
            g.add((e69_e52, EOTB, Literal(datetime(c["annee_deces_max"], 12, 31), datatype=XSD.date)))

print("ŒUVRES", end="")
oeuvres_genres = requests.get(f"{BASE_URI}/items/oeuvres_genres?{param_at}&limit=-1").json()["data"]
oeuvres = requests.get(f"{BASE_URI}/items/oeuvres?{param_at}&limit=-1").json()["data"]
print(f" ({len(oeuvres)})")
for o in oeuvres:
    print("    ", o['id'], "", end="")
    print(o["titre"])
    f1_uuid = o["id"]
    f1 = URIRef(f1_uuid)

    # Œuvre
    g.add((f1, RDF.type, lrmoo_ns["F1_Work"]))

    # Genre
    for og_id in o["genres"]:
        genre = URIRef(list(filter(lambda x: x["id"] == og_id, oeuvres_genres))[0]["genres_id"])
        g.add((f1, crm_ns["P2_has_type"], genre))

    # Titre
    if o["titre"]:
        g.add((f1, doremus_ns["U70_has_original_title"], Literal(o["titre"])))

print("PARTITIONS", end="")
oeuvres_compositeurs = requests.get(f"{BASE_URI}/items/oeuvres_compositeurs?{param_at}&limit=-1").json()["data"]
partitions = requests.get(f"{BASE_URI}/items/partitions?{param_at}&limit=-1").json()["data"]
print(f" ({len(partitions)})")
for p in partitions:
    print("    ", p["id"], p["pre_sherlock_url"])
    f2_uuid = p["id"]
    f2 = URIRef(f2_uuid)
    f1 = URIRef(p["oeuvre"])

    # F2
    g.add((f2, RDF.type, lrmoo_ns["F2_Expression"]))
    g.add((f1, lrmoo_ns["R3_is_realised_in"], f2))

    # MEI file pre SHERLOCK URL
    e42_pre_sherlock_url = URIRef(cache.get_uuid(["partitions", f2_uuid, "e42_pre_sherlock_url", "uuid"], True))
    g.add((e42_pre_sherlock_url, RDF.type, crm_ns["E42_Identifier"]))
    g.add((f2, crm_ns["P1_is_identified_by"], e42_pre_sherlock_url))
    g.add((e42_pre_sherlock_url, crm_ns["P190_has_symbolic_content"], URIRef(p["pre_sherlock_url"])))

    # MEI file post SHERLOCK URL
    e42_post_sherlock_url = URIRef(cache.get_uuid(["partitions", f2_uuid, "e42_post_sherlock_url", "uuid"], True))
    g.add((e42_post_sherlock_url, RDF.type, crm_ns["E42_Identifier"]))
    g.add((f2, crm_ns["P1_is_identified_by"], e42_post_sherlock_url))
    g.add((e42_post_sherlock_url, crm_ns["P190_has_symbolic_content"], URIRef(f"https://data-iremus.huma-num.fr/files/modality-tonality/mei/{f2}.mei")))

    # F28 Expression Creation
    f28 = URIRef(cache.get_uuid(["oeuvres", f2_uuid, "f28", "uuid"], True))
    g.add((f28, RDF.type, lrmoo_ns["F28_Expression_Creation"]))
    g.add((f28, lrmoo_ns["R17_created"], f2))
    g.add((f28, lrmoo_ns["R19_created_a_realisation_of"], f1))
    compositeurs = map(
        lambda x: x["compositeurs_id"],
        (filter(lambda x: x["oeuvres_id"] == p["oeuvre"], oeuvres_compositeurs))
    )
    for c in compositeurs:
        compositeur = URIRef(c)
        e7 = URIRef(cache.get_uuid(["partitions", f2_uuid, "compositeurs", c, "e7", "uuid"], True))
        g.add((f28, crm_ns["P9_consists_of"], e7))
        g.add((e7, RDF.type, crm_ns["E7_Activity"]))
        g.add((e7, crm_ns["P14_carried_out_by"], compositeur))
        g.add((e7, lrmoo_ns["M31_Actor_Function"], DOREMUS_COMPOSER))


# That's all folks!
cache.bye()
serialization = g.serialize(format="turtle", base="http://data-iremus.huma-num.fr/id/")
with open(args.ttl, "w+") as f:
    f.write(serialization)
