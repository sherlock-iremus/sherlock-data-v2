import argparse
import json
import os
from pathlib import PurePath
from rdflib import XSD, Graph, Literal, Namespace, RDF, RDFS, URIRef, DCTERMS
import requests
import sys
import yaml
from sherlockcachemanagement import Cache

################################################################################
# SETUP
################################################################################

parser = argparse.ArgumentParser()
parser.add_argument("--analysis_ontology")
parser.add_argument("--cache")
parser.add_argument("--historical_models_dir")
parser.add_argument("--out_ttl")
parser.add_argument("--researcher_uuid")
args = parser.parse_args()

cache = Cache(args.cache)

crm = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
crmdig = Namespace('http://www.cidoc-crm.org/crmdig/')
lrmoo = Namespace('http://www.cidoc-crm.org/lrmoo/')
sherlock = Namespace('http://data-iremus.huma-num.fr/id/')
sherlockns = Namespace('http://data-iremus.huma-num.fr/ns/sherlock#')
zarlino1588 = Namespace("http://modality-tonality.huma-num.fr/Zarlino_1558#")

g_in = Graph()
g_in.parse(args.analysis_ontology)
MTNS = ''
bindings = g_in.query("SELECT ?s WHERE { ?s rdf:type owl:Ontology }")
for binding in bindings:
    MTNS = str(binding.s + '#')
g_in.bind("mtao", MTNS)

M21NS = "http://modality-tonality.huma-num.fr/music21#"
g_out = Graph()
g_out.bind("crm", str(crm))
g_out.bind("crmdig", str(crmdig))
g_out.bind("lrmoo", lrmoo)
g_out.bind("music21", M21NS)
g_out.bind("mtao", MTNS)
g_out.bind("sherlock", str(sherlock))
g_out.bind("sherlockns", str(sherlockns))
g_out.bind("zarlino1588", zarlino1588)

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

# Récupération des données Directus


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

mei_file_to_score_uuid = {}
for partition in result["data"]["partitions"]:
    mei_file_to_score_uuid[PurePath(partition["pre_sherlock_url"]).name] = partition["id"]

################################################################################
# PROCESS
################################################################################

analyses = g_in.query(f"SELECT * WHERE {{ ?s a <{MTNS}Analysis> }}")
for analysis in analyses:
    analysis_key = URIRef(analysis[0])

    # Software

    origin = g_in.query(f"SELECT * WHERE {{ <{analysis_key}> <{MTNS}hasOrigin> ?o }}").bindings[0]['o']
    pythonModuleName = g_in.query(f"SELECT * WHERE {{ <{origin}> <{MTNS}hasPythonModuleName> ?o }}").bindings[0]['o']
    pythonClassName = g_in.query(f"SELECT * WHERE {{ <{origin}> <{MTNS}hasPythonClassName> ?o }}").bindings[0]['o']
    pythonDefName = g_in.query(f"SELECT * WHERE {{ <{origin}> <{MTNS}hasPythonDefName> ?o }}").bindings[0]['o']
    software = URIRef(cache.get_uuid(["D14", pythonModuleName+'•'+pythonClassName+'•'+pythonDefName, "uuid"], True))
    g_out.add((software, RDF.type, crmdig["D14_Software"]))
    g_out.add((software, RDF.type, crm["E39_Actor"]))
    g_out.add((software, URIRef(MTNS+"hasPythonModuleName"), Literal(pythonModuleName)))
    g_out.add((software, URIRef(MTNS+"hasPythonClassName"), Literal(pythonClassName)))
    g_out.add((software, URIRef(MTNS+"hasPythonDefName"), Literal(pythonDefName)))
    g_out.add((software, crm["P2_has_type"], URIRef("29b00e39-75da-4945-b6c4-a0ca00f96f68")))

    # Software execution

    software_execution = URIRef(cache.get_uuid(["D14", pythonModuleName+'•'+pythonClassName+'•'+pythonDefName, "D10", "uuid"], True))
    g_out.add((software_execution, RDF.type, crmdig["D10_Software_Execution"]))
    g_out.add((software_execution, crmdig["L23_used_software_or_firmware"], software))
    # TODO g_out.add((software_execution, crmdig["L2_used_as_source"], ))
    # TODO g_out.add((software_execution, crmdig["L10_had_input"], ))
    # TODO g_out.add((software_execution, crmdig["L11_had_output"], ))
    software_date = g_in.query(f"SELECT * WHERE {{ <{origin}> <{MTNS}hasDate> ?o . }}").bindings[0]['o']
    software_date = Literal(software_date, datatype=XSD.dateTime)
    g_out.add((software_execution, DCTERMS["created"], software_date))

    # For later use…

    main_software = software

    # Analytical project

    analytical_project = URIRef(cache.get_uuid(["analyses", analysis_key, "E7", "uuid"], True))
    g_out.add((analytical_project, RDF.type, crm["E7_Activity"]))
    g_out.add((analytical_project, crm["P2_has_type"], URIRef("f122c08a-5084-4a94-80ed-019102976309")))  # E55 « Projet analytique »
    g_out.add((analytical_project, crm["P14_carried_out_by"], URIRef(args.researcher_uuid)))
    g_out.add((analytical_project, crm["P16_used_specific_object"], software))

    date = g_in.query(f"SELECT * WHERE {{ <{analysis_key}> <{MTNS}hasDate> ?o . }}").bindings[0]['o']
    g_out.add((analytical_project, DCTERMS["created"], Literal(
        date, datatype=XSD.dateTime)))

    # Work

    work = g_in.query(f"SELECT * WHERE {{ ?work <{MTNS}hasAnalysis> <{analysis_key}> }}").bindings[0]['work']
    work_triples = g_in.query(f"SELECT * WHERE {{ <{work}> ?p ?o }}").bindings
    for binding in work_triples:
        if str(binding["p"]) == MTNS + "hasURL":
            mei_file = str(binding["o"]).replace("https://raw.githubusercontent.com/guillotel-nothmann/", "").replace("/main", "")
            mei_file = PurePath(mei_file).name
            work = sherlock[URIRef(mei_file_to_score_uuid[mei_file])]
            g_out.add((analytical_project, crm["P16_used_specific_object"], work))

    # Theoretical model

    theoretical_model_iri = URIRef(g_in.query(f"SELECT * WHERE {{ <{analysis_key}> <{MTNS}hasTheoreticalModel> ?tm . ?tm <{MTNS}hasIRI> ?iri }}").bindings[0]['iri'])
    theoretical_model_name = g_in.query(f"SELECT * WHERE {{ <{analysis_key}> <{MTNS}hasTheoreticalModel> ?tm . ?tm <{MTNS}hasName> ?name }}").bindings[0]['name']
    g_out.add((theoretical_model_iri, RDF.type, lrmoo["F2_Work"]))
    g_out.add((theoretical_model_iri, crm["P1_is_identified_by"], Literal(theoretical_model_name)))
    g_out.add((theoretical_model_iri, crm["P2_has_type"], URIRef("ae6c2f18-c8ae-4fac-83c8-9486fd00db2c")))  # E55 « Traité théorique »
    g_out.add((analytical_project, crm["P33_used_specific_technique"], theoretical_model_iri))

    # Annotations

    def make_software(annotation_body):
        origin = g_in.query(f"SELECT * WHERE {{ <{annotation_body}> <{MTNS}hasOrigin> ?o }}").bindings[0]['o']
        pythonModuleName = g_in.query(f"SELECT * WHERE {{ <{origin}> <{MTNS}hasPythonModuleName> ?o }}").bindings[0]['o']
        pythonClassName = g_in.query(f"SELECT * WHERE {{ <{origin}> <{MTNS}hasPythonClassName> ?o }}").bindings[0]['o']
        pythonDefName = g_in.query(f"SELECT * WHERE {{ <{origin}> <{MTNS}hasPythonDefName> ?o }}").bindings[0]['o']
        software = URIRef(cache.get_uuid(["D14", pythonModuleName+'•'+pythonClassName+'•'+pythonDefName, "uuid"], True))
        g_out.add((software, RDF.type, crmdig["D14_Software"]))
        g_out.add((software, RDF.type, crm["E39_Actor"]))
        g_out.add((software, URIRef(MTNS+"hasPythonModuleName"), Literal(pythonModuleName)))
        g_out.add((software, URIRef(MTNS+"hasPythonClassName"), Literal(pythonClassName)))
        g_out.add((software, URIRef(MTNS+"hasPythonDefName"), Literal(pythonDefName)))
        g_out.add((software, crm["P2_has_type"], sherlock["fd434edb-66c1-4b0a-9b1f-f1aa136c705a"]))
        g_out.add((main_software, crm["P106_is_composed_of"], software))

        # Software execution
        software_execution = URIRef(cache.get_uuid(["D14", pythonModuleName+'•'+pythonClassName+'•'+pythonDefName, "D10", "uuid"], True))
        g_out.add((software_execution, RDF.type, crmdig["D10_Software_Execution"]))
        g_out.add((software_execution, crmdig["L23_used_software_or_firmware"], software))
        # TODO g_out.add((software_execution, crmdig["L2_used_as_source"], ))
        # TODO g_out.add((software_execution, crmdig["L10_had_input"], ))
        # TODO g_out.add((software_execution, crmdig["L11_had_output"], ))
        software_date = g_in.query(f"SELECT * WHERE {{ <{origin}> <{MTNS}hasDate> ?o . }}").bindings[0]['o']
        software_date = Literal(software_date, datatype=XSD.dateTime)
        g_out.add((software_execution, DCTERMS["created"], software_date))

    annotations = g_in.query(f"SELECT * WHERE {{ <{analysis_key}> <{MTNS}hasAnalyticalObservation> ?ao . ?ao ?p ?a }}").bindings
    for a in annotations:
        annotation_body = a["a"]
        annotation_id = annotation_body.split("#")[-1]

        if str(a["p"]).startswith("http://modality-tonality.huma-num.fr/"):

            p = str(a["p"].split("#")[-1])
            analytical_entity_id = str(a["a"].split("#")[-1])

            # Software
            make_software(annotation_body)

            # Création de l'entité analytique
            analytical_entity = URIRef(cache.get_uuid(["analyses", analysis_key, "analytical_entities", analytical_entity_id, "uuid"], True))
            g_out.add((analytical_entity, RDF["type"], crm["E28_Conceptual_Object"]))
            g_out.add((analytical_entity, crm["P2_has_type"], URIRef("6d72746a-9f28-4739-8786-c6415d53c56d")))

            if p == "hasCadence":

                # Création de la sélection
                selection = URIRef(cache.get_uuid(["analyses", analysis_key, "annotations", annotation_id, "selection", "uuid"], True))
                g_out.add((selection, RDF["type"], crm["E28_Conceptual_Object"]))
                g_out.add((selection, crm["P2_has_type"], sherlock["9d0388cb-a178-46b2-b047-b5a98f7bdf0b"]))
                g_out.add((selection, DCTERMS.creator, main_software))
                g_out.add((selection, DCTERMS.created, Literal(software_date, datatype=XSD.dateTime)))
                g_out.add((selection, sherlockns["has_document_context"], work))

                # Création de l'E13 reliant la sélection à l'entité analytique
                e13 = URIRef(cache.get_uuid(["analyses", analysis_key, "annotations", annotation_id, "e13", "uuid"], True))
                g_out.add((e13, RDF.type, crm["E13_Attribute_Assignment"]))
                g_out.add((e13, crm["P140_assigned_attribute_to"], selection))
                g_out.add((e13, crm["P177_assigned_property_of_type"], a["p"]))
                g_out.add((e13, crm["P141_assigned"], analytical_entity))
                g_out.add((e13, sherlockns["has_document_context"], work))
                g_out.add((e13, crm["P33_used_specific_technique"], theoretical_model_iri))
                g_out.add((e13, crm["P14_carried_out_by"], software))
                g_out.add((e13, DCTERMS["created"], software_date))
                g_out.add((analytical_project, crm["P9_consists_of"], e13))

                # Recherche de tous les prédicats de l'entité anlytique
                po_list = g_in.query(f"SELECT * WHERE {{ <{annotation_body}> ?p ?o }}").bindings
                for po in po_list:
                    if str(po["p"]) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type":
                        if str(po["o"]).startswith("http://modality-tonality.huma-num.fr/"):
                            e13 = URIRef(cache.get_uuid(["analyses", analysis_key, "annotations", annotation_id, "e13_types", po["o"].split("/")[-1], "uuid"], True))
                            g_out.add((e13, RDF.type, crm["E13_Attribute_Assignment"]))
                            g_out.add((e13, crm["P140_assigned_attribute_to"], analytical_entity))
                            g_out.add((e13, crm["P177_assigned_property_of_type"], RDF.type))
                            g_out.add((e13, crm["P141_assigned"], URIRef(po["o"])))
                            g_out.add((e13, sherlockns["has_document_context"], work))
                            g_out.add((e13, crm["P33_used_specific_technique"], theoretical_model_iri))
                            g_out.add((e13, DCTERMS["created"], software_date))
                            g_out.add((e13, crm["P14_carried_out_by"], software))
                            g_out.add((analytical_project, crm["P9_consists_of"], e13))
                    elif str(po["p"]) != "http://modality-tonality.huma-num.fr/analysisOntology#hasOrigin":
                        note_id = g_in.query(f"SELECT * WHERE {{ <{po['o']}> <{M21NS+'id'}> ?id }}").bindings
                        note = URIRef(work.split(
                            "/")[-1] + "_" + str(note_id[0]["id"]))

                        # Ajout de la note à la sélection
                        g_out.add(
                            (selection, crm["P106_is_composed_of"], note))

                        # Rattachement de la note à l'entité analytique
                        e13 = URIRef(cache.get_uuid(["analyses", analysis_key, "annotations", annotation_id, "e13_p", po["p"].split("/")[-1], "uuid"], True))
                        g_out.add((e13, RDF.type, crm["E13_Attribute_Assignment"]))
                        g_out.add((e13, crm["P140_assigned_attribute_to"], analytical_entity))
                        g_out.add((e13, crm["P177_assigned_property_of_type"], URIRef(po["p"])))
                        g_out.add((e13, crm["P141_assigned"], note))
                        g_out.add((e13, sherlockns["has_document_context"], work))
                        g_out.add((e13, crm["P33_used_specific_technique"], theoretical_model_iri))
                        g_out.add((e13, DCTERMS["created"], software_date))
                        g_out.add((e13, crm["P14_carried_out_by"], software))
                        g_out.add((analytical_project, crm["P9_consists_of"], e13))

            elif p in ["bassusHasAmbitus", "cantusHasAmbitus", "tenorHasAmbitus"]:
                e13 = URIRef(cache.get_uuid(["analyses", analysis_key, "annotations", annotation_id, "e13", "uuid"], True))
                g_out.add((e13, RDF.type, crm["E13_Attribute_Assignment"]))
                g_out.add((e13, crm["P140_assigned_attribute_to"], work))
                g_out.add((e13, crm["P177_assigned_property_of_type"], URIRef(a["p"])))
                g_out.add((e13, sherlockns["has_document_context"], work))
                g_out.add((e13, crm["P33_used_specific_technique"], theoretical_model_iri))
                g_out.add((e13, DCTERMS["created"], software_date))
                g_out.add((e13, crm["P14_carried_out_by"], software))
                # print(annotation_body)
            else:
                print(p)

################################################################################
# THAT'S ALL FOLKS
################################################################################

cache.bye()
g_out.serialize(format='turtle', destination=args.out_ttl, base=sherlock)