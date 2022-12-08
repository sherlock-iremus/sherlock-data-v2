import argparse
from lxml import etree
from lxml.etree import tostring
import os
from rdflib import Graph, Literal as l, Namespace, RDF, RDFS, URIRef as u, XSD
import pathlib
import re
import uuid
import sys
import yaml
from pathlib import Path, PurePath
from sherlockcachemanagement import Cache

sys.path.append(os.path.abspath(os.path.join("rdfizers/", "")))
from helpers_rdf import *  # nopep8

parser = argparse.ArgumentParser()
parser.add_argument("--tei")
parser.add_argument("--output_ttl")
parser.add_argument("--cache_tei")
args = parser.parse_args()

cache_tei = Cache(args.cache_tei)
init_graph()

################################################################################
# DONNEES STATIQUES
################################################################################

# F18

F18 = she(cache_tei.get_uuid(["Corpus", "F18", "uuid"], True))
t(F18, RDF.type, lrm("F18_Serial_Work"))
t(F18, crm("P1_is_identified_by"), l("Mercure Galant"))

# JDDV

jddv = she("86f2088f-a2d3-43f7-9bbc-72a2601635cf")
t(jddv, RDF.type, crm("E21_Person"))
t(jddv, crm("P1_is_identified_by"), l("Jean Donneau de Visé"))
bnf_e42 = u("ark:/12148/cb119003987")
t(jddv, crm("P1_is_identified_by"), bnf_e42)
t(bnf_e42, RDF.type, crm("E42_Identifier"))
t(bnf_e42, crm("P2_has_type"), u("b89767f1-38fe-4a9e-9b4d-ea1d5624a687"))  # type lien data.bnf.fr
t(bnf_e42, crm("P190_has_symbolic_content"), u("https://data.bnf.fr/ark:/12148/cb119003987"))

# F27

F27_F18 = she(cache_tei.get_uuid(["Corpus", "F18", "F27"], True))
t(F27_F18, RDF.type, lrm("F27_Work_Conception"))
t(F27_F18, lrm("R16_initiated"), F18)
t(F27_F18, crm("P14_carried_out_by"), jddv)

tei_ns = {"tei": "http://www.tei-c.org/ns/1.0"}

for file in os.listdir(args.tei):
    if pathlib.Path(file).suffix != ".xml":
        continue

    try:
        tree = etree.parse(os.path.join(args.tei, file))
    except:
        print("Fichier pourri :", file)
        continue

    root = tree.getroot()

    ################################################################################
    # LIVRAISON
    ################################################################################

    # Work
    livraison_id = file[3:-4]
    livraison_titre = root.xpath("//tei:titleStmt/tei:title/text()", namespaces=tei_ns)[0]
    livraison_F1 = she(cache_tei.get_uuid(["Corpus", "Livraisons", livraison_id, "F1"], True))
    t(F18, lrm("R10_has_member"), livraison_F1)
    t(livraison_F1, RDF.type, lrm("F1_Work"))
    t(livraison_F1, crm("P1_is_identified_by"), l(livraison_titre))

    # Expression originale
    livraison_F2_originale = she(cache_tei.get_uuid(["Corpus", "Livraisons", livraison_id, "Expression originale", "F2"], True))
    t(livraison_F1, lrm("R3_is_realised_in"), livraison_F2_originale)
    t(livraison_F2_originale, RDF.type, lrm("F2_Expression"))
    t(livraison_F2_originale, crm("P2_has_type"), she("7d7fc017-61ba-4f80-88e1-744f1d00dd60"))
    t(livraison_F2_originale, crm("P2_has_type"), she("901c2bb5-549d-47e9-bd91-7a21d7cbe49f"))

    # Manifestation de l'expression originale
    livraison_F3 = she(cache_tei.get_uuid(["Corpus", "Livraisons", livraison_id, "Expression originale", "F3"], True))
    t(livraison_F3, RDF.type, lrm("F3_Manifestation"))
    t(livraison_F3, lrm("R4_embodies"), livraison_F2_originale)
    # Date de publication
    livraison_F3_F30 = she(cache_tei.get_uuid(["Corpus", "Livraisons", livraison_id, "Expression originale", "F3_F30"], True))
    t(livraison_F3_F30, RDF.type, lrm("F30_Manifestation_Creation"))
    t(livraison_F3_F30, lrm("R24_created"), livraison_F3)
    livraison_F3_E52 = she(cache_tei.get_uuid(["Corpus", "Livraisons", livraison_id, "Expression originale", "F3_E52"], True))
    t(livraison_F3_E52, RDF.type, crm("E52_Time-Span"))
    livraison_F3_date = root.xpath("string(//tei:creation/tei:date/@when)", namespaces=tei_ns)
    # Si la date @when ne comporte pas de mois, on va le chercher dans l'identifiant du fichier TEI
    if len(livraison_F3_date) == 4:
        livraison_F3_date = livraison_id[:7]
    t(livraison_F3_E52, crm("P82b_end_of_the_end"), l(livraison_F3_date + "-01T00:00:00", datatype=XSD.dateTime))
    t(livraison_F3_F30, crm("P4_has_time-span"), livraison_F3_E52)

    # Expression TEI
    livraison_F2_tei = she(cache_tei.get_uuid(["Corpus", "Livraisons", livraison_id, "Expression TEI", "F2"], True))
    t(livraison_F2_tei, RDF.type, lrm("F2_Expression"))
    t(livraison_F2_tei, RDF.type, crmdig("D1_Digital_Object"))
    t(livraison_F2_tei, RDF.type, crm("E31_Document"))
    t(livraison_F1, lrm("R3_is_realised_in"), livraison_F2_tei)
    t(livraison_F2_tei, she_ns("same_interpretative_content"), livraison_F2_originale)
    t(livraison_F2_originale, she_ns("same_interpretative_content"), livraison_F2_tei)

    # URL du fichier TEI
    livraison_F2_tei_E42 = she(cache_tei.get_uuid(["Corpus", "Livraisons", livraison_id, "Expression TEI", "F2_E42"], True))
    t(livraison_F2_tei, crm("P1_is_identified_by"), livraison_F2_tei_E42)
    t(livraison_F2_tei_E42, RDF.type, crm("E42_Identifier"))
    t(livraison_F2_tei_E42, crm("P2_has_type"), she("219fd53d-cdf2-4174-8d71-6d12bdd24016"))
    t(livraison_F2_tei_E42, crm("P190_has_symbolic_content"), u(f"http://data-iremus.huma-num.fr/files/mercure-galant/tei/livraisons/{file[0:-4]}.xml"))

    # Identifiant de la TEI
    livraison_F2_tei_E42_id = she(cache_tei.get_uuid(["Corpus", "Livraisons", livraison_id, "Expression TEI", "F2_E42_id"], True))
    t(livraison_F2_tei, crm("P1_is_identified_by"), livraison_F2_tei_E42_id)
    t(livraison_F2_tei_E42_id, RDF.type, crm("E42_Identifier"))
    t(livraison_F2_tei_E42_id, crm("P2_has_type"), she("92c258a0-1e34-437f-9686-e24322b95305"))
    t(livraison_F2_tei_E42_id, crm("P190_has_symbolic_content"), l(livraison_id))

    # Creation de l'expression TEI
    livraison_F2_tei_F28 = she(cache_tei.get_uuid(["Corpus", "Livraisons", livraison_id, "Expression TEI", "F2_F28"], True))
    t(livraison_F2_tei_F28, RDF.type, lrm("F28_Expression_Creation"))
    t(livraison_F2_tei_F28, lrm("R17_created"), livraison_F2_tei)
    t(livraison_F2_tei_F28, crm("P16_used_specific_object"), livraison_F2_originale)
    t(livraison_F2_tei_F28, crm("P14_carried_out_by"), she("684b4c1a-be76-474c-810e-0f5984b47921"))
    t(livraison_F2_tei_F28, crm("P2_has_type"), she("9acad7ae-1335-4ab4-b79c-489319e5d595"))  # type « Encodage TEI »

    ################################################################################
    # ARTICLES
    ################################################################################

    div = root.xpath('//tei:body//tei:div[@type="article"]', namespaces=tei_ns)
    for article in div:

        article_titre_xpath = article.xpath("./tei:head/child::node()", namespaces=tei_ns)
        article_id = article.attrib["{http://www.w3.org/XML/1998/namespace}id"][3:]
        article_titre = ""
        for node in article_titre_xpath:
            if type(node) == etree._ElementUnicodeResult:
                article_titre += re.sub(r"\s+", " ", node.replace("\n", ""))
            if type(node) == etree._Element:
                if node.tag == "{http://www.tei-c.org/ns/1.0}hi":
                    article_titre += re.sub(r"\s+", " ", node.text.replace("\n", ""))

        # Expression originale
        article_F2_original = she(cache_tei.get_uuid(["Corpus", "Livraisons", livraison_id, "Expression originale", "Articles", article_id, "F2",], True))
        t(article_F2_original, RDF.type, lrm("F2_Expression"))
        t(article_F2_original, crm("P1_is_identified_by"), l(article_titre))
        t(article_F2_original, crm("P2_has_type"), she("13f43e00-680a-4a6d-a223-48e8d9bbeaae"))  # type « Article »
        t(article_F2_original, crm("P2_has_type"), she("7d7fc017-61ba-4f80-88e1-744f1d00dd60"))  # type « Édition originale »
        t(livraison_F2_originale, crm("P148_has_component"), article_F2_original)

        # Expression TEI
        article_F2_tei = she(cache_tei.get_uuid(["Corpus", "Livraisons", livraison_id, "Expression TEI", "Articles", article_id, "F2",], True))
        t(article_F2_tei, RDF.type, lrm("F2_Expression"))
        t(article_F2_tei, RDF.type, crm("E31_Document"))
        t(article_F2_tei, RDF.type, crmdig("D1_Digital_Object"))
        t(livraison_F2_tei, crm("P148_has_component"), article_F2_tei)
        t(article_F2_tei, crm("P2_has_type"), she("13f43e00-680a-4a6d-a223-48e8d9bbeaae"))  # type « Article »
        t(article_F2_tei, crm("P2_has_type"), she("62b49ca2-ec73-4d72-aaf3-045da6869a15"))  # édition « TEI »
        t(article_F2_tei, she_ns("same_interpretative_content"), article_F2_original)
        t(article_F2_original, she_ns("same_interpretative_content"), article_F2_tei)

        # Identifiant de l'expression TEI
        article_F2_tei_E42 = she(cache_tei.get_uuid(["Corpus", "Livraisons", livraison_id, "Expression TEI", "Articles", article_id, "F2_E42",], True))
        t(article_F2_tei, crm("P1_is_identified_by"), article_F2_tei_E42)
        t(article_F2_tei_E42, RDF.type, crm("E42_Identifier"))
        t(article_F2_tei_E42, crm("P190_has_symbolic_content"), l(article_id))

        # Récupération des notes éditoriales et création des E13
        notes_editoriales = []
        for element in article.iter("{http://www.tei-c.org/ns/1.0}note"):
            if element.get("resp") == "editor":
                content = ("".join(element.itertext()).replace("\n", "").replace("\t", ""))
                content = re.sub(" +", " ", content)
                notes_editoriales.append(content)

        n = 1
        for note in notes_editoriales:
            E13_note_editoriale = she(cache_tei.get_uuid(["Corpus", "Livraisons", livraison_id, "Expression TEI", "Articles", article_id, f"E13 note éditoriale n°{n}",], True))
            t(E13_note_editoriale, crm("P14_carried_out_by"), she("684b4c1a-be76-474c-810e-0f5984b47921"))
            t(E13_note_editoriale, RDF.type, crm("E13_Attribute_Assignement"))
            t(E13_note_editoriale, crm("P140_assigned_attribute_to"), article_F2_original)
            t(E13_note_editoriale, crm("P141_assigned"), l(note))
            t(E13_note_editoriale, crm("P177_assigned_property_of_type"), she_ns("has_editorial_note"))
            n += 1


#####################################################################################################
# ECRITURE DU TTL
#####################################################################################################

save_graph(args.output_ttl)

cache_tei.bye()
