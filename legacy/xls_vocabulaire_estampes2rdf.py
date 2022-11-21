# On utilise les listes et non les dictionnaires car on a plusieurs colonnes "terme spécifique" (=> donc duplication des keys)

import argparse
from slugify import slugify
from rdflib import Graph, Namespace, DCTERMS, RDF, RDFS, SKOS, URIRef, XSD, URIRef as u, Literal as l
from openpyxl import load_workbook
from pprint import pprint
import yaml
import sys
import pandas as pd
import numpy as np
from numpy import nan

# ARGUMENTS
parser = argparse.ArgumentParser()
parser.add_argument("--xlsx")
parser.add_argument("--ttl")
args = parser.parse_args()

# INSTANCIATION DU GRAPHE
g = Graph()
g.bind("dcterms", DCTERMS)
g.bind("skos", SKOS)
opentheso_ns = Namespace("https://opentheso.huma-num.fr/opentheso/")
g.bind("opentheso", opentheso_ns)


def t(s, p, o):
    g.add((s, p, o))


def opth(x):
    return opentheso_ns[x]


a = RDF.type

###########################################################################################################
# CREATION DES DONNEES
###########################################################################################################

# Fichier Excel
vocabulaire = pd.read_excel(args.xlsx)
vocabulaire.dropna()
rows = vocabulaire.values.tolist()

# Le vocabulaire (E32)
cs_iri = opth("generated_thesaurus_identifier")
g.add((cs_iri, SKOS.prefLabel, l("Vocabulaire d'indexation des estampes")))
g.add((cs_iri, RDF.type, SKOS.ConceptScheme))
g.add((cs_iri, DCTERMS.language, l("fr")))
g.add((cs_iri, DCTERMS.title, l("[Mercure Galant] Vocabulaire d'indexation des estampes")))

# Cache qui servira à l'indexation des estampes
concepts_uuid = {}

erreurs = []

for row in rows:
    row[2:6] = [None if type(x) == float else x for x in row[2:6]]
    concept_str = row[5] or row[4] or row[3] or row[2] or row[1]
    pprint(concept_str)
    concept_uri = opth(slugify(concept_str))

    t(concept_uri, a, SKOS.Concept)
    t(concept_uri, DCTERMS.identifier, l(slugify(concept_str)))
    t(concept_uri, SKOS.prefLabel, l(concept_str))
    t(concept_uri, SKOS.inScheme, cs_iri)

    lignee = list(filter(lambda x: x, row[1:6]))
    g.add((cs_iri, SKOS.hasTopConcept, opth(slugify(lignee[0]))))
    g.add((opth(slugify(lignee[-1])), SKOS.inScheme, cs_iri))

    for i in range(0, len(lignee)-1):
        g.add((opth(slugify(lignee[i])), SKOS.narrower, opth(slugify(lignee[i+1]))))
        g.add((opth(slugify(lignee[i+1])), SKOS.broader, opth(slugify(lignee[i]))))

###########################################################################################################
# CREATION DU FICHIER TURTLE
###########################################################################################################

serialization = g.serialize(format="turtle", base="https://opentheso.huma-num.fr/opentheso/")
with open(args.ttl, "w+") as f:
    f.write(serialization)
