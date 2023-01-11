from sherlockcachemanagement import Cache
import argparse
import sys
import os
from pprint import pprint
from slugify import slugify
import requests
import yaml
import json
import re

# Regex

pattern_article = re.compile("MG-[0-9]{4}-[0-9]{2}[a-zA-Z]?_[0-9]{3}")
pattern_livraison = re.compile("[0-9]{4}-[0-9]{2}[a-zA-Z]?")
pattern_lieu_opentheso = re.compile("^[0-9]{1,6}$")
pattern_lien = re.compile("(https?[^ ]+)")

# Helpers
sys.path.append(os.path.abspath(os.path.join('rdfizers/', '')))
from helpers_rdf import *  # nopep8
sys.path.append(os.path.abspath(os.path.join('python_packages/helpers_excel', '')))
from helpers_excel import *  # nopep8
sys.path.append(os.path.abspath(os.path.join('directus/', '')))
from helpers_graphql_api import graphql_query  # nopep8

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--ttl")
parser.add_argument("--xlsx")
parser.add_argument("--opentheso_id")  # opth Thesaurus id ?
parser.add_argument("--cache")
parser.add_argument("--cache_tei")
parser.add_argument("--directus_secret")
args = parser.parse_args()

# Directus secret
file = open(args.directus_secret)
secret = yaml.full_load(file)

# Caches
cache = Cache(args.cache)
if args.cache_tei:
    cache_tei = Cache(args.cache_tei)

# Initialisation du graphe
init_graph()

print("Récupération des personnes via l'API directus...")

personnes_directus = graphql_query("""
query {
  personnes(limit: -1) {
    id
  } 
}""", secret)

print("Récupération des lieux via l'API directus...")

lieux_directus = graphql_query("""
query {
  lieux(limit: -1) {
    id
    opentheso_id
  } 
}""", secret)

print("Récupération du vocabulaire d'indexation via l'API opentheso...")

r = requests.get(f"https://opentheso.huma-num.fr/opentheso/api/all/theso?id={args.opentheso_id}&format=jsonld", stream=True)
skos_data = json.loads(r.text)
concept_uris_list = [concept["@id"] for concept in skos_data]


def make_E13(cache_key, p140, p177, p141):
    e13 = she(cache.get_uuid(cache_key, True))
    t(e13, a, crm("E13_Attribute_Assignement"))
    t(e13, crm("P14_carried_out_by"), equipe_mercure_galant_uri)
    t(e13, crm("P140_assigned_attribute_to"), p140)
    t(e13, crm("P141_assigned"), p141)
    t(e13, crm("P177_assigned_property_of_type"), p177)

    return e13

#######################################################################################################
# Traitement des estampes
#######################################################################################################


rows = get_xlsx_rows_as_dicts(args.xlsx)


for row in rows:

    if row["ID estampe"] is not None:
        id_livraison = pattern_livraison.search(row["ID estampe"]).group(0)

        # Dans le cas où la livraison n'aurait jamais été transcrite en TEI, on se donne le droit de la référencer dans le cache
        livraison_F2_originale = she(cache_tei.get_uuid(["Corpus", "Livraisons", id_livraison, "Expression originale", "F2"], True))

        concepts_used = []
        personnes_used = []
        lieux_used = []
        id = row["ID estampe"]

        # region E36: Estampe
        estampe = she(cache.get_uuid(["estampes", id, "E36_uuid"], True))
        t(estampe, a, crm("E36_Visual_Item"))
        t(corpus_estampes_uri, crm("P106_is_composed_of"), estampe)
        t(estampe, crm("P2_has_type"), estampe_e55_uri)
        # endregion

        # region E42: Identifiant Mercure Galant de l'estampe
        E42_uuid = she(cache.get_uuid(["estampes", id, "E42_mercure_uuid"], True))
        t(E42_uuid, a, crm("E42_Identifier"))
        t(E42_uuid, crm("P2_has_type"), identifiant_mercure_e55_uri)
        t(E42_uuid, crm("P190_has_symbolic_content"), l(id))
        t(estampe, crm("P1_is_identified_by"), E42_uuid)
        # endregion

        # region E42: Identifiant IIIF de l'estampe
        E42_iiif = she(cache.get_uuid(["estampes", id, "E42_IIIF_humanum_uuid"], True))
        t(E42_iiif, a, crm("E42_Identifier"))
        t(E42_iiif, crm("P2_has_type"), identifiant_iiif_e55_uri)
        t(E42_iiif, crm("P190_has_symbolic_content"), u(f"https://ceres.huma-num.fr/iiif/3/mercure-galant-estampes--{id.replace(' ', '%20')}/full/max/0/default.jpg"))
        t(estampe, crm("P1_is_identified_by"), E42_iiif)
        # endregion

        # region F2: Rattachement à la livraison ou à l'article
        if row["ID article OBVIL"]:
            match = pattern_article.search(row["ID article OBVIL"])
            if match:
                try:
                    id_article = match.group(0)[3:]
                    article_F2_original = she(cache_tei.get_uuid(["Corpus", "Livraisons", id_livraison, "Expression originale", "Articles", id_article, "F2"]))
                    article_F2_TEI = she(cache_tei.get_uuid(["Corpus", "Livraisons", id_livraison, "Expression TEI", "Articles", id_article, "F2"]))
                    t(article_F2_original, crm("P106_is_composed_of"), estampe)
                    t(article_F2_TEI, crm("P106_is_composed_of"), estampe)
                except:
                    print("[Colonne ID article OBVIL] Article TEI inexistant : " + id_article)
            else:
                try:
                    livraison_F2_TEI = she(cache_tei.get_uuid(["Corpus", "Livraisons", id_livraison, "Expression TEI", "F2"]))
                    t(livraison_F2_originale, crm("P106_is_composed_of"), estampe)
                    t(livraison_F2_TEI, crm("P106_is_composed_of"), estampe)
                except:
                    print("[Colonne ID estampe] Livraison TEI inexistante : " + id_livraison)
        # endregion

        # region F2: Article annexe à la gravure
        if row["ID OBVIL article lié"]:
            match = pattern_article.search(row["ID OBVIL article lié"])
            if match:
                id_article_lie = match.group(0)[3:]
                id_livraison = pattern_livraison.search(id_article_lie).group(0)
                try:
                    article_F2_TEI = she(cache_tei.get_uuid(["Corpus", "Livraisons", id_livraison, "Expression TEI", "Articles", id_article_lie, "F2"]))
                    e13 = make_E13(["estampes", id, "seeAlso", "E13_uuid"], estampe, RDFS.seeAlso, article_F2_TEI)
                    if row["Commentaire ID article lié OBVIL"]:
                        t(e13, crm("P3_has_note"), l(row["Commentaire ID article lié OBVIL"]))
                except:
                    print("[Colonne ID OBVIL article lié] Article TEI inexistant : " + id_article_lie)
        # endregion

        # region seeAlso: Lien vers le texte en ligne
        cell_content = (row["Lien vers le texte [ou l'image] en ligne"] or "").strip()
        if cell_content:
            matches = re.findall(pattern_lien, cell_content)
            for url in matches:
                if url.startswith("https://gallica.bnf.fr/"):
                    E42_gallica = she(cache.get_uuid(["estampes", id, "E42_gallica_uuid"], True))
                    t(E42_gallica, RDF.type, crm("E42_Identifier"))
                    t(E42_gallica, crm("P190_has_symbolic_content"), u(url))
                    t(E42_gallica, crm("P2_has_type"), lien_gallica_e55_uri)
                    t(estampe, RDFS.seeAlso, E42_gallica)
                else:
                    t(estampe, RDFS.seeAlso, u(url))

            # on crée une note si la cellule ne se résume pas à une URL
            if not matches or matches[0] != cell_content:
                t(estampe, crm("P3_has_note"), l(cell_content))
        # endregion

        # region E13: Titre sur l'image
        if row["Titre sur l'image"]:
            make_E13(["estampes", id, "E13_titre_sur_l_image_uuid"], estampe, titre_sur_l_image_e55_uri, l(row["Titre sur l'image"]))
        # endregion

        # region E13: Titre descriptif/forgé
        if row["[titre descriptif forgé]* (Avec Maj - accentuées]"]:
            titre = row["[titre descriptif forgé]* (Avec Maj - accentuées]"].replace("[", "").replace("]", "").replace("*", "")
            make_E13(["estampes", id, "E13_titre_forgé_uuid"], estampe, titre_descriptif_forge_e55_uri, l(titre))
        # endregion

        # region E13: Titre dans le péritexte
        if row["[Titre dans le péritexte: Avis, article…]"]:
            titre = row["[Titre dans le péritexte: Avis, article…]"].replace("[", "").replace("]", "").replace("*", "")
            make_E13(["estampes", id, "E13_titre_péritexte_uuid"], estampe, she(titre_peritexte_e55_uri), l(titre))
        # endregion

        # region E13: Lieux associés
        if row["Lieux/Etats associés"]:
            lieux = row["Lieux/Etats associés"]
            for lieu_label in lieux.split(";"):
                lieu = lieu_label.lstrip().split(' ')[0]
                if (lieu == ''):
                    continue
                match = pattern_lieu_opentheso.search(lieu)
                # Transformer ID opentheso en uuid directus
                if (match):
                    lieu = next((x["id"] for x in lieux_directus["data"]["lieux"] if x["opentheso_id"] == int(match.group(0))), None)
                if (not lieu):
                    print(f"Aucun lieu trouvé dans Directus pour : {lieu_label}")
                    continue
                make_E13(["collection", id, "lieux associés", lieu, "E13_uuid"], estampe, lieu_associe_e55_uri, she(lieu))
                lieux_used.append(lieu)
        # endregion

        # region E13-P138: Lieux représentés
        if row["Lieux représentés"]:
            lieux = row["Lieux représentés"]
            for lieu_label in lieux.split(";"):
                lieu = lieu_label.lstrip().split(' ')[0]
                if (lieu == ''):
                    continue
                match = pattern_lieu_opentheso.search(lieu)
                # Transformer ID opentheso en uuid directus
                if (match):
                    lieu = next((x["id"] for x in lieux_directus["data"]["lieux"] if x["opentheso_id"] == int(match.group(0))), None)
                if (not lieu):
                    print(f"Aucun lieu trouvé dans Directus pour : {lieu_label}")
                    continue

                estampe_fragment = she(cache.get_uuid(["estampes", id, "lieux représentés", lieu, "E36_fragment", "uuid"], True))
                estampe_fragment_e42_iiif = she(cache.get_uuid(["estampes", id, "lieux représentés", lieu, "E36_fragment", "E42_IIIF_humanum_uuid"], True))

                t(estampe_fragment, a, crm("E36_Visual_Item"))
                t(estampe_fragment, she_ns("is_fragment_of"), estampe)
                t(estampe_fragment_e42_iiif, crm("P2_has_type"), identifiant_iiif_e55_uri)
                t(estampe_fragment_e42_iiif, RDF.type, crm("E42_Identifier"))

                make_E13(["estampes", id, "lieux représentés", lieu, "E36_fragment", "E13_IIIF_uuid"], estampe_fragment, crm("P1_is_identified_by"), estampe_fragment_e42_iiif)
                make_E13(["estampes", id, "lieux représentés", lieu, "E36_fragment", "E13_P138_uuid"], estampe_fragment, crm("P138_represents"), she(lieu))
                lieux_used.append(lieu)
        # endregion

        # region E13: Thématique de la gravure
        if row["Thématique [Avec Maj et au pl.]"]:
            thématiques = row["Thématique [Avec Maj et au pl.]"].split(";")
            for thématique in thématiques:
                thématique = thématique.strip().replace("’", "'")
                if thématique == "" or thématique == " ":
                    continue
                thématique_uri = opth(slugify(thématique), args.opentheso_id)
                concepts_used.append(thématique_uri)
                make_E13(["collection", id, "thématiques", thématique, "E13_uuid"], estampe, thematique_e55_uri, thématique_uri)
        # endregion

        # region E13-P138: Objet représenté
        if row["Objets représentés"]:
            objets = row["Objets représentés"].split(";")
            for objet in objets:
                objet = objet.strip().replace("’", "'")
                if objet == "" or objet == " ":
                    continue

                objet_type_uri = opth(slugify(objet), args.opentheso_id)
                concepts_used.append(objet_type_uri)

                estampe_fragment = she(cache.get_uuid(["estampes", id, "objets", objet, "E36_fragment", "uuid"], True))
                estampe_fragment_e42_iiif = she(cache.get_uuid(["estampes", id, "objets", objet, "E36_fragment", "E42_IIIF_humanum_uuid"], True))
                e18_objet = she(cache.get_uuid(["estampes", id, "objets", objet, "E36_fragment", "E18_uuid"], True))

                t(estampe_fragment, a, crm("E36_Visual_Item"))
                t(estampe_fragment, she_ns("is_fragment_of"), estampe)
                t(estampe_fragment_e42_iiif, crm("P2_has_type"), identifiant_iiif_e55_uri)
                t(estampe_fragment_e42_iiif, a, crm("E42_Identifier"))
                t(e18_objet, a, crm("E18_Physical_Thing"))
                t(e18_objet, crm("P2_has_type"), objet_type_uri)

                make_E13(["estampes", id, "objets", objet, "E36_fragment", "E13_IIIF_uuid"], estampe_fragment, crm("P1_is_identified_by"), estampe_fragment_e42_iiif)
                make_E13(["estampes", id, "objets", objet, "E36_fragment", "E13_P138_uuid"], estampe_fragment, crm("P138_represents"), e18_objet)

                # Si l'objet est une médaille et comporte une inscription
                if objet == "médaille" and (row["Médailles: avers"] or row["Médailles: revers"]):
                    if row["Médailles: avers"]:
                        estampe_fragment_avers = she(cache.get_uuid(["estampes", id, "objets", objet, "E36_fragment", "médaille_avers", "E36_uuid"], True))
                        estampe_fragment_avers_e42_iiif = she(cache.get_uuid(["estampes", id, "objets", objet, "E36_fragment", "médaille_avers", "E42_IIIF_humanum_uuid"], True))
                        e18_avers = she(cache.get_uuid(["estampes", id, "objets", objet, "E36_fragment", "médaille_avers", "E18_uuid"], True))
                        e34_inscription = she(cache.get_uuid(["estampes", id, "objets", objet, "E36_fragment", "médaille_avers", "inscription", "uuid"], True))

                        t(estampe_fragment_avers, a, crm("E36_Visual_Item"))
                        t(estampe_fragment_avers, she_ns("is_fragment_of"), estampe_fragment)
                        t(e18_objet, crm("P46_is_composed_of"), e18_avers)
                        t(e18_avers, a, crm("E18_Physical_Thing"))
                        t(e18_avers, crm("P2_has_type"), avers_medaille_e55_uri)
                        t(estampe_fragment_avers_e42_iiif, crm("P2_has_type"), identifiant_iiif_e55_uri)
                        t(estampe_fragment_avers_e42_iiif, a, crm("E42_Identifier"))
                        t(e34_inscription, a, crm("E34_Inscription"))
                        t(e18_avers, crm("P165_incorporates"), e34_inscription)

                        make_E13(["estampes", id, "objets", objet, "E36_fragment", "médaille_avers", "E42_IIIF_humanum_uuid"], estampe_fragment_avers, crm("P1_is_identified_by"), estampe_fragment_avers_e42_iiif)
                        make_E13(["estampes", id, "objets", objet, "E36_fragment", "médaille_avers", "E13_P138_uuid"], estampe_fragment_avers, crm("P138_represents"), e18_avers)
                        make_E13(["estampes", id, "objets", objet, "E36_fragment", "médaille_avers", "inscription", "E13_uuid"], e34_inscription, crm("P190_has_symbolic_content"), l(row["Médailles: avers"]))

                    # Si la médaille comporte une inscription sur son revers (E13)
                    if row["Médailles: revers"]:
                        estampe_fragment_revers = she(cache.get_uuid(["estampes", id, "objets", objet, "E36_fragment", "médaille_revers", "E36_uuid"], True))
                        estampe_fragment_revers_e42_iiif = she(cache.get_uuid(["estampes", id, "objets", objet, "E36_fragment", "médaille_revers", "E42_IIIF_humanum_uuid"], True))
                        e18_revers = she(cache.get_uuid(["estampes", id, "objets", objet, "E36_fragment", "médaille_revers", "E18_uuid"], True))
                        e34_inscription = she(cache.get_uuid(["estampes", id, "objets", objet, "E36_fragment", "médaille_revers", "inscription", "uuid"], True))

                        t(estampe_fragment_revers, a, crm("E36_Visual_Item"))
                        t(estampe_fragment_revers, she_ns("is_fragment_of"), estampe_fragment)
                        t(e18_objet, crm("P46_is_composed_of"), e18_revers)
                        t(e18_revers, a, crm("E18_Physical_Thing"))
                        t(e18_revers, crm("P2_has_type"), revers_medaille_e55_uri)
                        t(estampe_fragment_revers_e42_iiif, crm("P2_has_type"), identifiant_iiif_e55_uri)
                        t(estampe_fragment_revers_e42_iiif, a, crm("E42_Identifier"))
                        t(e34_inscription, a, crm("E34_Inscription"))
                        t(e18_revers, crm("P165_incorporates"), e34_inscription)

                        make_E13(["estampes", id, "objets", objet, "E36_fragment", "médaille_revers", "E42_IIIF_humanum_uuid"], estampe_fragment_revers, crm("P1_is_identified_by"), estampe_fragment_revers_e42_iiif)
                        make_E13(["estampes", id, "objets", objet, "E36_fragment", "médaille_revers", "E13_P138_uuid"], estampe_fragment_revers, crm("P138_represents"), e18_revers)
                        make_E13(["estampes", id, "objets", objet, "E36_fragment", "médaille_revers", "inscription", "E13_uuid"], e34_inscription, crm("P190_has_symbolic_content"), l(row["Médailles: revers"]))
        # endregion

        # region E13-P138: Personnes représentées
        if row["Personnes représentées"]:
            personnes = row["Personnes représentées"].split(";")
            for personne in personnes:
                personne = personne.strip().replace("’", "'")
                if personne == "" or personne == " ":
                    continue
                estampe_fragment = she(cache.get_uuid(["estampes", id, "personnes représentées", personne, "E36_fragment", "uuid"], True))
                estampe_fragment_e42_iiif = she(cache.get_uuid(["estampes", id, "personnes représentées", personne, "E36_fragment", "E42_IIIF_humanum_uuid"], True))
                e21_personne = she(personne)

                personnes_used.append(personne)
                make_E13(["estampes", id, "personnes représentées", personne, "E36_fragment", "E13_IIIF_uuid"], estampe_fragment, crm("P1_is_identified_by"), estampe_fragment_e42_iiif)
                make_E13(["estampes", id, "personnes représentées", personne, "E36_fragment", "E13_P138_uuid"], estampe_fragment, crm("P138_represents"), e21_personne)
        # endregion

        # region E13: Personnes associées
        if row["Personnes associées"]:
            personnes = row["Personnes associées"].split(";")
            for personne in personnes:
                personne = personne.strip().replace("’", "'")
                if personne == "" or personne == " ":
                    continue
                personnes_used.append(personne)
                make_E13(["estampes", id, "personnes associées", personne, "E13_uuid"], estampe, personne_associee_e55_uri, she(personne))
        # endregion

        # region E65: Production de l'estampe
        if row["Inventeur (du sujet) ['Invenit' ou 'Pinxit' ou 'Delineavit']"] or row[
                "Graveur ['Sculpsit' ou 'Incidit' ou 'fecit']"]:
            estampe_E65 = she(cache.get_uuid(["estampes", id, "E65", "uuid"], True))
            t(estampe_E65, a, crm("E65_Creation"))
            t(estampe_E65, crm("P94_has_created"), estampe)
        # endregion

        # region sous-E65: Invenit (concepteur de l'estampe)
        if row["Inventeur (du sujet) ['Invenit' ou 'Pinxit' ou 'Delineavit']"]:
            estampe_invenit = she(cache.get_uuid(["estampes", id, "E65", "E65_invenit", "uuid"], True))
            t(estampe_invenit, a, crm("E65_Creation"))
            t(estampe_invenit, crm("P2_has_type"), invenit_e55_uri)
            t(estampe_E65, crm("P9_consists_of"), estampe_invenit)

            # Lien entre conception de l'estampe et concepteur (E13)
            concepteur_uuid = row["Inventeur (du sujet) ['Invenit' ou 'Pinxit' ou 'Delineavit']"].strip().lower()
            make_E13(["estampes", id, "E65", "E65_invenit", "E13_P14_uuid"], estampe_invenit, crm("P14_carried_out_by"), she(concepteur_uuid))
        # endregion

        # region sous-E65: Sculpsit (graveur de l'estampe)
        if row["Graveur ['Sculpsit' ou 'Incidit' ou 'fecit']"]:
            estampe_sculpsit = she(cache.get_uuid(["estampes", id, "E65", "E65_sculpsit", "uuid"], True))
            t(estampe_sculpsit, a, crm("E65_Creation"))
            t(estampe_sculpsit, crm("P2_has_type"), sculpsit_e55_uri)
            t(estampe_E65, crm("P9_consists_of"), estampe_sculpsit)

            # Lien entre la gravure de l'estampe et son graveur (E13)
            graveur_uuid = row["Graveur ['Sculpsit' ou 'Incidit' ou 'fecit']"].strip().lower()
            make_E13(["estampes", id, "E65", "E65_sculpsit", "E13_P14_uuid"], estampe_sculpsit, crm("P14_carried_out_by"), she(graveur_uuid))
        # endregion

        # region E13: Type de représentation
        if row["Types de représentation"]:
            types = row["Types de représentation"].split(";")
            for type_label in types:
                if type_label == "" or type_label == " ":
                    continue
                slug = slugify(type_label.strip().replace("’", "'"))
                type_uri = opth(slug, args.opentheso_id)
                concepts_used.append(type_uri)
                make_E13(["estampes", id, "types de représentation", slug, "E13_uuid"], estampe, type_representation_e55_uri, type_uri)
        # endregion

        # region E13: Technique de gravure
        if row["Technique de la gravure"]:
            techniques = row["Technique de la gravure"].split(",")
            for technique_label in techniques:
                if technique_label == "" or technique_label == " ":
                    continue
                slug = slugify(technique_label.strip().replace("’", "'"))
                technique_uri = opth(slug, args.opentheso_id)
                concepts_used.append(technique_uri)
                make_E13(["estampes", id, "technique de la gravure", slug, "E13_uuid"], estampe, technique_de_gravure_e55_uri, technique_uri)
        # endregion

        # region E13-P70: Bibliographie relative à l'estampe
        if row["BIBLIO [y compris liens] relative à la gravure et aux artistes"]:
            make_E13(["estampes", id, "bibliographie", "E13_P70_uuid"], estampe, e55_note_bibliographique, l(row["BIBLIO [y compris liens] relative à la gravure et aux artistes"]))
        # endregion

        # region Exemplaire physique
        livraison_F3_consultation = u(cache.get_uuid(["livraisons", id_livraison, "F3_consultation_uuid"], True))
        livraison_F5_consultation = u(cache.get_uuid(["livraisons", id_livraison, "F5_consultation_uuid"], True))
        E24_feuille = u(cache.get_uuid(["livraisons", id_livraison, "E24_feuille_uuid"], True))

        t(livraison_F3_consultation, lrm("R4_embodies"), livraison_F2_originale)
        t(livraison_F2_originale, lrm("R4i_is_embodied_in"), livraison_F3_consultation)
        t(livraison_F5_consultation, lrm('R7_is_materialization_of'), livraison_F3_consultation)
        t(livraison_F3_consultation, lrm('R7i_is_materialized_in'), livraison_F5_consultation)
        t(livraison_F5_consultation, crm("P46_is_composed_of"), E24_feuille)
        t(E24_feuille, crm("P46i_forms_part_of"), livraison_F5_consultation)
        t(E24_feuille, crm("P65_shows_visual_item"), estampe)

        # Provenance cliché (identifiant BnF)
        if row["Provenance cliché"]:
            E42_provenance = she(cache.get_uuid(["livraisons", id_livraison, "E42_provenance_uuid"], True))
            t(E42_provenance, a, crm("E42_Identifier"))
            t(E42_provenance, crm("P2_has_type"), cote_bnf_e55_uri)
            t(E42_provenance, crm("P190_has_symbolic_content"), l(row["Provenance cliché"]))
            t(livraison_F5_consultation, crm("P1_is_identified_by"), E42_provenance)

        # Format
        if row["Format (H x L en cm)"]:
            format = row["Format (H x L en cm)"].split("x")
            hauteur_uri = she(cache.get_uuid(["livraisons", id_livraison, id, "E54_hauteur", "uuid"], True))
            t(hauteur_uri, a, crm("E54_Dimension"))
            t(hauteur_uri, crm("P2_has_type"), u("http://vocab.getty.edu/page/aat/300055644"))
            t(hauteur_uri, crm("P90_has_value"), l(format[0].strip().replace("’", "'")))
            t(hauteur_uri, crm("P91_has_unit"), u("http://vocab.getty.edu/page/aat/300379098"))
            make_E13(["livraisons", id_livraison, id, "E54_hauteur", "E13_P43_dimension_uuid"], E24_feuille, crm("P43_has_dimension"), hauteur_uri)

            largeur_uri = she(cache.get_uuid(["livraisons", id_livraison, id, "E54_largeur", "uuid"], True))
            t(largeur_uri, a, crm("E54_Dimension"))
            t(largeur_uri, crm("P2_has_type"), u("http://vocab.getty.edu/page/aat/300055647"))
            t(largeur_uri, crm("P90_has_value"), l(format[1].replace("cm", "").strip().replace("’", "'")))
            t(largeur_uri, crm("P91_has_unit"), u("http://vocab.getty.edu/page/aat/300379098"))
            make_E13(["livraisons", id_livraison, id, "E54_largeur", "E13_P43_dimension_uuid"], E24_feuille, crm("P43_has_dimension"), largeur_uri)
        # endregion

        # region TESTS
        for concept in concepts_used:
            if (str(concept) not in concept_uris_list):
                print(f"[Concept manquant] {concept[45:][:-10]} ({row['ID estampe']})")
        for personne_uuid in personnes_used:
            if (not next((x for x in personnes_directus["data"]["personnes"] if x["id"] == personne_uuid), None)):
                print(f"[Personne manquante] {personne_uuid} ({row['ID estampe']})")
        for lieu_uuid in lieux_used:
            if (not next((x for x in lieux_directus["data"]["lieux"] if x["id"] == lieu_uuid), None)):
                print(f"[Lieu manquant] {lieu_uuid} ({row['ID estampe']})")
        # endregion


###########################################################################################################
# Création du graphe et du cache
###########################################################################################################

cache.bye()
cache_tei.bye()
save_graph(args.ttl)

# TODO ROADBLOACKED INSTITUTIONS : en attente de la saisie des institutions dans directus (stagiaire printemps 2023)
# TODO sherlock data constants
