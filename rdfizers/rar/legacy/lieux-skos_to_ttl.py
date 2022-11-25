import argparse
import hashlib
import os
from pathlib import Path, PurePath
from types import prepare_class
from rdflib import Graph, Namespace, DCTERMS, RDF, RDFS, SKOS, URIRef as u, Literal as l
import re
import sys
import uuid
import yaml
from sherlockcachemanagement import Cache
import unidecode

parser = argparse.ArgumentParser()
parser.add_argument("--inputrdf")
parser.add_argument("--output_ttl")
parser.add_argument("--cache_lieux")
parser.add_argument("--cache_tei")
parser.add_argument("--label_uuid")
args = parser.parse_args()

label_uuid = {}

# CACHE

cache_tei = Cache(args.cache_tei)
cache_lieux = Cache(args.cache_lieux)

################################################################################
# Initialisation des graphes
################################################################################

input_graph = Graph()
input_graph.load(args.inputrdf)

output_graph = Graph()

crm_ns = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
crmdig_ns = Namespace("http://www.ics.forth.gr/isl/CRMdig/")
iremus_ns = Namespace("http://data-iremus.huma-num.fr/id/")
lrmoo_ns = Namespace("http://www.cidoc-crm.org/lrmoo/")
sdt_ns = Namespace("http://data-iremus.huma-num.fr/datatypes/")
sherlock_ns = Namespace("http://data-iremus.huma-num.fr/ns/sherlock#")

output_graph.bind("crm", crm_ns)
output_graph.bind("crmdig", crmdig_ns)
output_graph.bind("dcterms", DCTERMS)
output_graph.bind("lrmoo", lrmoo_ns)
output_graph.bind("sdt", sdt_ns)
output_graph.bind("she_ns", sherlock_ns)
output_graph.bind("skos", SKOS)

a = RDF.type


def crm(x):
    return u(crm_ns[x])


def dig(x):
    return u(crmdig_ns[x])


def lrm(x):
    return u(lrmoo_ns[x])


def she(x):
    return u(iremus_ns[x])

def she_ns(x):
    return u(sherlock_ns[x])


def t(s, p, o):
    output_graph.add((s, p, o))


def ro(s, p):
    try:
        return list(input_graph.objects(s, p))[0]
    except:
        return None


def ro_list(s, p):
    try:
        return list(input_graph.objects(s, p))
    except:
        return None


def census_label_uuid(label, uuid):
    global label_uuid

    label = str(label).lower().replace('\n', '').replace('é', 'e',).replace('è', 'e',).replace('le ', '').replace('la ', '')
    while "  " in label:
        label = label.replace("  ", " ")
    uuid = str(uuid)

    if label in label_uuid:
        if uuid not in label_uuid[label]:
            #print("HOMONYMIE :", label, uuid, label_uuid[label])
            label_uuid[label].append(uuid)
    else:
        label_uuid[label] = [uuid]


def explore(id, depth, sous_E32):
    # print("    " * depth, id)

    # E93 Presence
    identifier = ro(id, DCTERMS.identifier)
    if identifier and identifier != "1336" and identifier != "275949":
        E93_uuid = cache_lieux.get_uuid(["lieux", identifier, "E93", "uuid"], True)
        E93_uri = she(E93_uuid)
        t(E93_uri, a, crm("E93_Presence"))
        t(E32_lieux_uri, crm("P71_lists"), E93_uri)
        t(sous_E32, crm("P71_lists"), E93_uri)

        # DCTERMS.created/modified
        t(E93_uri, DCTERMS.created, ro(id, DCTERMS.created))
        t(E93_uri, DCTERMS.modified, ro(id, DCTERMS.modified))

        # E41_Appellation
        E41_uri = she(cache_lieux.get_uuid(["lieux", identifier, "E93", "E41"], True))
        t(E93_uri, crm("P1_is_identified_by"), E41_uri)
        t(E41_uri, a, crm("E41_Appellation"))
        for prefLabel in ro_list(id, SKOS.prefLabel):
            t(E41_uri, RDFS.label, prefLabel)
            t(E41_uri, crm("P2_has_type"), SKOS.prefLabel)
            census_label_uuid(prefLabel, E93_uuid)
        altLabels = ro_list(id, SKOS.altLabel)
        if len(altLabels) > 0:
            for altLabel in altLabels:
                E41_alt_uri = she(cache_lieux.get_uuid(["lieux", identifier, "E93", "E41_alt", altLabel], True))
                t(E41_alt_uri, a, crm("E41_Appellation"))
                t(E41_alt_uri, RDFS.label, altLabel)
                t(E93_uri, crm("P1_is_identified_by"), E41_alt_uri)
                t(E41_alt_uri, crm("P2_has_type"), SKOS.altLabel)
                census_label_uuid(altLabel, E93_uuid)


        # E13 Indexation
        def process_note(p):
            values = ro_list(id, p)
            for v in values:
                if "##id##" in v:
                    v = v.split("##id##")
                    for v in v:
                        if v:
                            m = re.search(indexation_regexp, v)
                            m_livraison = re.search(indexation_regexp_livraison, v)
                            if m:
                                clef_mercure_livraison = m_livraison.group()[3:]
                                clef_mercure_article = m.group()[3:]
                                try:
                                    F2_article_uri = she(cache_tei.get_uuid(
                                        ["Corpus", "Livraisons", clef_mercure_livraison, "Expression TEI", "Articles",
                                         clef_mercure_article, "F2"]))
                                    E13_index_uri = she(cache_lieux.get_uuid(["lieux", identifier, "E93", "indexation", "E13"], True))
                                    t(E13_index_uri, a, crm("E13_Attribute_Assignement"))
                                    t(E13_index_uri, DCTERMS.created, ro(id, DCTERMS.created))
                                    t(E13_index_uri, crm("P14_carried_out_by"), she("684b4c1a-be76-474c-810e-0f5984b47921"))
                                    t(E13_index_uri, crm("P140_assigned_attribute_to"), F2_article_uri)
                                    t(E13_index_uri, crm("P141_assigned"), E93_uri)
                                    t(E13_index_uri, crm("P177_assigned_property_of_type"), crm("P67_refers_to"))

                                except:
                                    print(identifier, ": l'article", clef_mercure_article, "n'existe pas")
                                    print(clef_mercure_livraison, clef_mercure_article)

                elif "##" in v:
                    v = v.split("##")
                    for v in v:
                        if v:
                            m = re.search(indexation_regexp, v)
                            m_livraison = re.search(indexation_regexp_livraison, v)
                            if m:
                                clef_mercure_livraison = m_livraison.group()[3:]
                                clef_mercure_article = m.group()[3:]
                                try:
                                    F2_article_uri = she(cache_tei.get_uuid(
                                        ["Corpus", "Livraisons", clef_mercure_livraison, "Expression TEI", "Articles",
                                         clef_mercure_article, "F2"]))
                                    E13_index_uri = she(cache_lieux.get_uuid(["lieux", identifier, "E93", "indexation", "E13"], True))
                                    t(E13_index_uri, a, crm("E13_Attribute_Assignement"))
                                    t(E13_index_uri, DCTERMS.created, ro(id, DCTERMS.created))
                                    t(E13_index_uri, crm("P14_carried_out_by"), she("684b4c1a-be76-474c-810e-0f5984b47921"))
                                    t(E13_index_uri, crm("P140_assigned_attribute_to"), F2_article_uri)
                                    t(E13_index_uri, crm("P141_assigned"), E93_uri)
                                    t(E13_index_uri, crm("P177_assigned_property_of_type"), crm("P67_refers_to"))

                                except:
                                    print(identifier, ": l'article", clef_mercure_article, "n'existe pas")
                                    print(clef_mercure_livraison, clef_mercure_article)

                else:
                    note_sha1_object = hashlib.sha1(v.encode())
                    note_sha1 = note_sha1_object.hexdigest()
                    E13_note_uri = she(cache_lieux.get_uuid(["lieux", identifier, "E93", "note", "E13"], True))
                    t(E13_note_uri, a, crm("E13_Attribute_Assignement"))
                    t(E13_note_uri, DCTERMS.created, ro(id, DCTERMS.created))
                    t(E13_note_uri, crm("P14_carried_out_by"), she("684b4c1a-be76-474c-810e-0f5984b47921"))
                    t(E13_note_uri, crm("P140_assigned_attribute_to"), E93_uri)
                    note_uri = she(cache_lieux.get_uuid(["lieux", identifier, "E93", "note", note_sha1], True))
                    t(note_uri, RDFS.label, l(v))
                    t(E13_note_uri, crm("P141_assigned"), note_uri)
                    t(E13_note_uri, crm("P177_assigned_property_of_type"), crm("P3_has_note"))

        for note in [SKOS.note, SKOS.historyNote, SKOS.definition]:
            process_note(note)

        # Exact et Close Matches
        exactMatches = ro_list(id, SKOS.exactMatch)
        for exactMatch in exactMatches:
            if exactMatch == "https://opentheso3.mom.fr/opentheso3/index.xhtml":
                continue
            E42_uri = she(cache_lieux.get_uuid(["lieux", identifier, "E42", exactMatch], True))
            t(E42_uri, a, crm("E42_Identifier"))
            t(E42_uri, RDFS.label, u(exactMatch))
            t(E93_uri, crm("P1_is_identified_by"), E42_uri)


        closeMatches = ro_list(id, SKOS.closeMatch)
        for closeMatch in closeMatches:
            t(E93_uri, SKOS.closeMatch, closeMatch)

        # Coordonnées géographiques
        E53_uri = she(cache_lieux.get_uuid(["lieux", identifier, "E93", "E53"], True))
        t(E93_uri, crm("P161_has_spatial_projection"), E53_uri)

        geolat = ro(id, u("http://www.w3.org/2003/01/geo/wgs84_pos#lat"))
        geolong = ro(id, u("http://www.w3.org/2003/01/geo/wgs84_pos#long"))
        if geolat != None and geolong != None:
            t(E53_uri, crm("P168_place_is_defined_by"), l(f"[{str(geolat)}, {str(geolong)}]"))

    # narrowers
    narrowers = ro_list(id, SKOS.narrower)

    for narrower in narrowers:
        # P10 falls within
        identifier_n = ro(narrower, DCTERMS.identifier)
        narrower_uuid = she(cache_lieux.get_uuid(["lieux", identifier_n, "E93", "uuid"], True))
        t(narrower_uuid, crm("P10_falls_within"), E93_uri)

        explore(narrower, depth + 1, sous_E32)

####################################################################################
# DONNÉES STATIQUES
####################################################################################


indexation_regexp = r"MG-[0-9]{4}-[0-9]{2}[a-zA-Z]?_[0-9]{1,3}[a-zA-Z]?"
indexation_regexp_livraison = r"MG-[0-9]{4}-[0-9]{2}[a-zA-Z]?"

E32_lieux_uri = u(iremus_ns["4e7cdc71-b834-412a-8cab-daa363a8334e"])
t(E32_lieux_uri, a, crm("E32_Authority_Document"))
t(E32_lieux_uri, crm("P1_is_identified_by"), l("Noms de lieux"))


####################################################################################
# THESAURUS "GRAND SIECLE"
####################################################################################

# Création du thésaurus "Grand Siècle"

E32_grand_siecle_uri = u(iremus_ns["78061430-df57-4874-8334-44ed215a112e"])
t(E32_grand_siecle_uri, a, crm("E32_Authority_Document"))
t(E32_grand_siecle_uri, crm("P1_is_identified_by"), l("Grand Siècle"))
t(E32_lieux_uri, she_ns("sheP_a_pour_entité_de_plus_haut_niveau"), E32_grand_siecle_uri)

explore(u("https://opentheso3.mom.fr/opentheso3/?idc=1336&idt=43"), 0, E32_grand_siecle_uri)


####################################################################################
# THESAURUS "MONDE CONTEMPORAIN"
####################################################################################

# Création du thésaurus "Monde Contemporain"

E32_mon_cont_uri = u(iremus_ns["41dd59e3-2f0c-4ef3-b08c-9606f33a4a48"])
t(E32_mon_cont_uri, a, crm("E32_Authority_Document"))
t(E32_mon_cont_uri, crm("P1_is_identified_by"), l("Monde contemporain"))
t(E32_lieux_uri, she_ns("sheP_a_pour_entité_de_plus_haut_niveau"), E32_mon_cont_uri)

explore(u("https://opentheso3.mom.fr/opentheso3/?idc=275949&idt=43"), 0, E32_mon_cont_uri)


####################################################################################
# ECRITURE DU CACHE ET DES TRIPLETS
####################################################################################

serialization = output_graph.serialize(format="turtle", base="http://data-iremus.huma-num.fr/id/")
with open(args.output_ttl, "w+") as f:
    f.write(serialization)

cache_lieux.bye()

with open(args.label_uuid, 'w', encoding='utf-8') as f:
    yaml.dump(label_uuid, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
